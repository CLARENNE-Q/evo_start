"""Plateforme de boutons sécurisés pour les commandes d'actionnement EVO-START."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import CoordinateurEvoStart

JOURNALISEUR = logging.getLogger(__name__)

CONFIGURATIONS_BOUTONS: dict[str, dict[str, str]] = {
    "remote_start": {
        "nom": "Démarrer le moteur",
        "icone": "mdi:car-key",
        "action": "start",
    },
    "remote_stop": {
        "nom": "Arrêter le moteur",
        "icone": "mdi:car-off",
        "action": "stop",
    },
}


async def async_setup_entry(
    hass: HomeAssistant,
    entree_configuration: ConfigEntry,
    async_ajouter_entites: AddEntitiesCallback,
) -> None:
    """Initialiser et enregistrer les boutons d'actionnement par véhicule."""
    coordinateur: CoordinateurEvoStart = hass.data[DOMAIN][entree_configuration.entry_id]
    liste_entites: list[BoutonActionneurEvoStart] = []

    for identifiant_vehicule in coordinateur.get_all_vehicle_ids():
        donnees_vehicule = coordinateur.get_vehicle_data(identifiant_vehicule) or {}
        nom_vehicule = donnees_vehicule.get("carinfo", {}).get(
            "cname", f"Véhicule {identifiant_vehicule}"
        )

        for cle_bouton, parametres in CONFIGURATIONS_BOUTONS.items():
            liste_entites.append(
                BoutonActionneurEvoStart(
                    coordinateur=coordinateur,
                    identifiant_vehicule=identifiant_vehicule,
                    cle_bouton=cle_bouton,
                    parametres_bouton=parametres,
                    nom_vehicule=nom_vehicule,
                )
            )

    async_ajouter_entites(liste_entites)


class BoutonActionneurEvoStart(CoordinatorEntity[CoordinateurEvoStart], ButtonEntity):
    """Représentation d'un bouton poussoir sécurisé avec verrouillage d'exécution."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinateur: CoordinateurEvoStart,
        identifiant_vehicule: str,
        cle_bouton: str,
        parametres_bouton: dict[str, str],
        nom_vehicule: str,
    ) -> None:
        """Instancier le composant bouton avec contrôle d'accès sécurisé."""
        super().__init__(coordinateur)
        self._identifiant_vehicule = identifiant_vehicule
        self._cle_bouton = cle_bouton
        self._parametres = parametres_bouton
        self._nom_vehicule = nom_vehicule

        self._attr_name = parametres_bouton["nom"]
        self._attr_unique_id = f"evo_start_{identifiant_vehicule}_{cle_bouton}"
        self._attr_icon = parametres_bouton["icone"]
        self._verrou_execution = asyncio.Lock()

    @property
    def device_info(self) -> DeviceInfo:
        """Associer l'entité au registre physique du véhicule."""
        return DeviceInfo(
            identifiers={(DOMAIN, f"evo_start_vehicle_{self._identifiant_vehicule}")},
            name=self._nom_vehicule,
            manufacturer="Fortin",
            model="EVO-START",
        )

    def _valider_regles_securite_physique(self, action: str) -> None:
        """Vérifier l'état mécanique avant d'autoriser l'envoi de la commande."""
        drapeaux = self.coordinator.get_vehicle_flags(self._identifiant_vehicule)
        if not drapeaux:
            return

        # Règle critique: Ne jamais démarrer si le capot avant est ouvert
        drapeau_capot = drapeaux.get("dor_frn")
        if action == "start" and drapeau_capot == "1":
            JOURNALISEUR.warning(
                "Refus de démarrage: le capot du véhicule %s est détecté ouvert",
                self._identifiant_vehicule,
            )
            raise HomeAssistantError("Impossible de démarrer: le capot moteur est ouvert.")

        # Vérification d'état moteur
        drapeau_moteur = drapeaux.get("vcl_eng")
        if drapeau_moteur is not None:
            moteur_en_marche = str(drapeau_moteur) == "1"
            if action == "start" and moteur_en_marche:
                raise HomeAssistantError("Le moteur du véhicule est déjà en marche.")
            if action == "stop" and not moteur_en_marche:
                raise HomeAssistantError("Le moteur du véhicule est déjà arrêté.")

    async def async_press(self) -> None:
        """Exécuter l'action demandée sous protection anti-rebond et TLS."""
        if self._verrou_execution.locked():
            JOURNALISEUR.info("Commande ignorée: une opération est déjà en cours d'envoi")
            return

        async with self._verrou_execution:
            type_action = self._parametres["action"]
            self._valider_regles_securite_physique(type_action)

            succes = False
            try:
                if type_action == "start":
                    succes = await self.coordinator.async_remote_start(
                        self._identifiant_vehicule
                    )
                elif type_action == "stop":
                    succes = await self.coordinator.async_remote_stop(
                        self._identifiant_vehicule
                    )

                if not succes:
                    raise HomeAssistantError(
                        f"Échec de transmission: la commande de {type_action} a été rejetée par le module."
                    )

                # Pause de stabilisation pour laisser le réseau cellulaire du véhicule répondre
                await asyncio.sleep(3)
                await self.coordinator.async_request_refresh()

            except HomeAssistantError:
                raise
            except Exception as erreur_inattendue:
                JOURNALISEUR.exception(
                    "Anomalie lors de l'exécution de l'action %s: %s",
                    type_action,
                    erreur_inattendue,
                )
                raise HomeAssistantError(
                    f"Erreur de communication avec le véhicule: {erreur_inattendue}"
                ) from erreur_inattendue


# Alias pour assurer la rétrocompatibilité
EvoStartButton = BoutonActionneurEvoStart
