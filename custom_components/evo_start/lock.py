"""Plateforme de verrouillage sécurisé pour les ouvrants EVO-START."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.components.lock import LockEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import CoordinateurEvoStart

JOURNALISEUR = logging.getLogger(__name__)

DELAI_PROPAGATION_CELLULAIRE_SECONDES = 2.5


async def async_setup_entry(
    hass: HomeAssistant,
    entree_configuration: ConfigEntry,
    async_ajouter_entites: AddEntitiesCallback,
) -> None:
    """Créer et enregistrer les entités de verrouillage centralisé pour chaque véhicule."""
    coordinateur: CoordinateurEvoStart = hass.data[DOMAIN][entree_configuration.entry_id]
    liste_verrous: list[VerrouCentraliseEvoStart] = []

    for identifiant_vehicule in coordinateur.get_all_vehicle_ids():
        donnees_vehicule = coordinateur.get_vehicle_data(identifiant_vehicule) or {}
        nom_vehicule = donnees_vehicule.get("carinfo", {}).get(
            "cname", f"Véhicule {identifiant_vehicule}"
        )

        liste_verrous.append(
            VerrouCentraliseEvoStart(
                coordinateur=coordinateur,
                identifiant_vehicule=identifiant_vehicule,
                nom_vehicule=nom_vehicule,
            )
        )

    async_ajouter_entites(liste_verrous)


class VerrouCentraliseEvoStart(CoordinatorEntity[CoordinateurEvoStart], LockEntity):
    """Représentation de la serrure centralisée avec validation stricte d'exécution."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_name = "Verrouillage centralisé"

    def __init__(
        self,
        coordinateur: CoordinateurEvoStart,
        identifiant_vehicule: str,
        nom_vehicule: str,
    ) -> None:
        """Initialiser le mécanisme de verrouillage distant."""
        super().__init__(coordinateur)
        self._identifiant_vehicule = identifiant_vehicule
        self._nom_vehicule = nom_vehicule
        self._attr_unique_id = f"evo_start_{identifiant_vehicule}_verrouillage_central"
        self._verrou_operation = asyncio.Lock()

    @property
    def device_info(self) -> DeviceInfo:
        """Lier l'entité au nœud physique du véhicule."""
        return DeviceInfo(
            identifiers={(DOMAIN, f"evo_start_vehicle_{self._identifiant_vehicule}")},
            name=self._nom_vehicule,
            manufacturer="Fortin",
            model="EVO-START",
        )

    @property
    def available(self) -> bool:
        """Déterminer la disponibilité selon l'état réel du coordinateur et des données."""
        if not super().available:
            return False
        return self._identifiant_vehicule in self.coordinator.vehicles_data

    @property
    def is_locked(self) -> bool | None:
        """Déduire l'état de verrouillage à partir des drapeaux binaires normalisés."""
        drapeaux = self.coordinator.get_vehicle_flags(self._identifiant_vehicule)
        if not drapeaux:
            return None

        # Dans le coordinateur sécurisé, le drapeau 'vcl_lok' est déjà normalisé: "1" = Verrouillé
        valeur_drapeau = drapeaux.get("vcl_lok")
        if valeur_drapeau not in ("0", "1"):
            return None

        return valeur_drapeau == "1"

    async def async_lock(self, **kwargs: Any) -> None:
        """Transmettre l'instruction de verrouillage avec contrôle d'acquittement."""
        if self._verrou_operation.locked():
            JOURNALISEUR.info("Instruction de verrouillage ignorée: commande en cours")
            return

        async with self._verrou_operation:
            succes = await self.coordinator.async_remote_lock(self._identifiant_vehicule)
            if not succes:
                JOURNALISEUR.error(
                    "Échec critique du verrouillage pour le véhicule %s",
                    self._identifiant_vehicule,
                )
                raise HomeAssistantError(
                    "Le module distant n'a pas confirmé le verrouillage des portes."
                )

            # Temporisation pour laisser l'actionneur mécanique et le réseau LTE se synchroniser
            await asyncio.sleep(DELAI_PROPAGATION_CELLULAIRE_SECONDES)
            await self.coordinator.async_request_refresh()

    async def async_unlock(self, **kwargs: Any) -> None:
        """Transmettre l'instruction de déverrouillage avec contrôle d'acquittement."""
        if self._verrou_operation.locked():
            JOURNALISEUR.info("Instruction de déverrouillage ignorée: commande en cours")
            return

        async with self._verrou_operation:
            succes = await self.coordinator.async_remote_unlock(self._identifiant_vehicule)
            if not succes:
                JOURNALISEUR.error(
                    "Échec critique du déverrouillage pour le véhicule %s",
                    self._identifiant_vehicule,
                )
                raise HomeAssistantError(
                    "Le module distant n'a pas confirmé le déverrouillage des portes."
                )

            await asyncio.sleep(DELAI_PROPAGATION_CELLULAIRE_SECONDES)
            await self.coordinator.async_request_refresh()


# Alias pour garantir la compatibilité descendante
EvoStartLock = VerrouCentraliseEvoStart
