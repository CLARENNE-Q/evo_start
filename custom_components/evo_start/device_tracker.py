"""Plateforme de géolocalisation et suivi GPS sécurisée pour l'intégration EVO-START."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.device_tracker import SourceType, TrackerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import CoordinateurEvoStart

JOURNALISEUR = logging.getLogger(__name__)

LIBELLES_DRAPEAUX: dict[str, str] = {
    "lig_smal": "feux_position",
    "lig_big": "feux_croisement",
    "dor_frn": "capot",
    "dor_rb": "porte_arriere_droite",
    "dor_rf": "porte_avant_droite",
    "dor_lb": "porte_arriere_gauche",
    "dor_lf": "porte_avant_gauche",
    "vcl_on2": "relais_auxiliaire_2",
    "vcl_on1": "relais_auxiliaire_1",
    "wnd_top": "toit_ouvrant",
    "wnd_rb": "vitre_arriere_droite",
    "wnd_rf": "vitre_avant_droite",
    "wnd_lb": "vitre_arriere_gauche",
    "vcl_anit": "antidemarrage",
    "vcl_repair": "mode_atelier",
    "vcl_air": "climatisation",
    "brk_fot": "frein_pied",
    "brk_han": "frein_stationnement",
    "gps_cls": "court_circuit_gps",
    "gps_opn": "circuit_ouvert_gps",
    "gps_loc": "signal_gps_actif",
    "gps_power": "alimentation_gps",
    "alm_tpms": "alerte_pression_pneus",
    "alm_bat": "alerte_tension_batterie",
    "alm_belt_m": "alerte_ceinture_securite",
    "alm_acc": "alerte_contact_anormal",
    "alm_dor": "alerte_intrusion_porte",
    "alm_vib": "alerte_choc_vibration",
    "alm_ultrasonic": "alerte_capteur_ultrasons",
    "alm_dor_open": "alerte_porte_non_verrouillee",
}


def extraire_coordonnee_valide(valeur_brute: Any) -> float | None:
    """Valider et convertir une coordonnée géographique en éliminant le point nul."""
    if valeur_brute is None or valeur_brute == "":
        return None
    try:
        coordonnee = float(valeur_brute)
        # Rejeter les coordonnées 0.0 (perte de fixation satellite) pour éviter Null Island
        if abs(coordonnee) < 0.0001:
            return None
        return coordonnee
    except (ValueError, TypeError):
        return None


async def async_setup_entry(
    hass: HomeAssistant,
    entree_configuration: ConfigEntry,
    async_ajouter_entites: AddEntitiesCallback,
) -> None:
    """Déployer l'entité de localisation géographique pour chaque véhicule."""
    coordinateur: CoordinateurEvoStart = hass.data[DOMAIN][entree_configuration.entry_id]
    liste_traceurs: list[TraceurVehiculeEvoStart] = []

    for identifiant_vehicule in coordinateur.get_all_vehicle_ids():
        donnees_vehicule = coordinateur.get_vehicle_data(identifiant_vehicule) or {}
        nom_vehicule = donnees_vehicule.get("carinfo", {}).get(
            "cname", f"Véhicule {identifiant_vehicule}"
        )

        liste_traceurs.append(
            TraceurVehiculeEvoStart(
                coordinateur=coordinateur,
                identifiant_vehicule=identifiant_vehicule,
                nom_vehicule=nom_vehicule,
            )
        )

    async_ajouter_entites(liste_traceurs)


class TraceurVehiculeEvoStart(CoordinatorEntity[CoordinateurEvoStart], TrackerEntity):
    """Représentation du traceur GPS du véhicule avec filtrage anti-dérive."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:car"

    def __init__(
        self,
        coordinateur: CoordinateurEvoStart,
        identifiant_vehicule: str,
        nom_vehicule: str,
    ) -> None:
        """Initialiser le traceur d'emplacement géographique."""
        super().__init__(coordinateur)
        self._identifiant_vehicule = identifiant_vehicule
        self._nom_vehicule = nom_vehicule
        self._attr_unique_id = f"evo_start_traceur_{identifiant_vehicule}"
        self._attr_name = "Position GPS"

    @property
    def device_info(self) -> DeviceInfo:
        """Lier le traceur au registre physique du véhicule."""
        return DeviceInfo(
            identifiers={(DOMAIN, f"evo_start_vehicle_{self._identifiant_vehicule}")},
            name=self._nom_vehicule,
            manufacturer="Fortin",
            model="EVO-START",
        )

    @property
    def source_type(self) -> SourceType:
        """Définir la nature de la source géodésique."""
        return SourceType.GPS

    @property
    def latitude(self) -> float | None:
        """Rapporter la latitude validée."""
        donnees = self.coordinator.get_vehicle_data(self._identifiant_vehicule)
        if not donnees:
            return None
        return extraire_coordonnee_valide(donnees.get("lloc", {}).get("lat"))

    @property
    def longitude(self) -> float | None:
        """Rapporter la longitude validée."""
        donnees = self.coordinator.get_vehicle_data(self._identifiant_vehicule)
        if not donnees:
            return None
        return extraire_coordonnee_valide(donnees.get("lloc", {}).get("lng"))

    @property
    def location_accuracy(self) -> int:
        """Renvoyer le rayon d'incertitude métrique pour les géolocalisations."""
        drapeaux = self.coordinator.get_vehicle_flags(self._identifiant_vehicule)
        # Si le signal GPS est verrouillé, précision de 15m; sinon dégradation à 100m
        if drapeaux.get("gps_loc") == "1":
            return 15
        return 100

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Exposer l'ensemble des drapeaux télémétriques de façon standardisée."""
        drapeaux = self.coordinator.get_vehicle_flags(self._identifiant_vehicule)
        donnees = self.coordinator.get_vehicle_data(self._identifiant_vehicule) or {}
        bloc_lloc = donnees.get("lloc", {})

        attributs: dict[str, Any] = {
            "vitesse_kmh": bloc_lloc.get("speed"),
            "horodatage_releve": bloc_lloc.get("gpstime"),
            "direction_degres": bloc_lloc.get("direction"),
        }

        # Injection des drapeaux sous forme de booléens natifs pour faciliter les scripts YAML
        for cle, valeur in drapeaux.items():
            if valeur in ("0", "1"):
                nom_attribut = LIBELLES_DRAPEAUX.get(cle, cle)
                attributs[nom_attribut] = valeur == "1"

        return attributs


# Alias pour préserver la rétrocompatibilité
EvoStartDeviceTracker = TraceurVehiculeEvoStart
