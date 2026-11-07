"""Point d'entrée principal et initialisation sécurisée du composant EVO-START."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN
from .coordinator import CoordinateurEvoStart

JOURNALISEUR = logging.getLogger(__name__)

# Liste centralisée des plateformes d'entités prises en charge
PLATEFORMES_SUPPORTEES: list[Platform] = [
    Platform.SENSOR,
    Platform.LOCK,
    Platform.DEVICE_TRACKER,
    Platform.BUTTON,
]


async def async_setup(hass: HomeAssistant, configuration: ConfigType) -> bool:
    """Initialiser le composant racine (conservé pour rétrocompatibilité du noyau)."""
    return True


async def async_setup_entry(
    hass: HomeAssistant, entree_configuration: ConfigEntry
) -> bool:
    """Initialiser et charger les entités associées à une entrée de configuration."""
    courriel = entree_configuration.data[CONF_EMAIL]
    mot_de_passe = entree_configuration.data[CONF_PASSWORD]

    coordinateur = CoordinateurEvoStart(
        hass=hass,
        courriel=courriel,
        mot_de_passe=mot_de_passe,
    )

    # Récupération initiale obligatoire des données télémétriques avant le montage des entités
    await coordinateur.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entree_configuration.entry_id] = coordinateur

    # Transmission synchrone et attendue aux gestionnaires de plateformes
    await hass.config_entries.async_forward_entry_setups(
        entree_configuration, PLATEFORMES_SUPPORTEES
    )

    return True


async def async_unload_entry(
    hass: HomeAssistant, entree_configuration: ConfigEntry
) -> bool:
    """Décharger proprement les entités et libérer les descripteurs de session."""
    dechargement_reussi = await hass.config_entries.async_unload_platforms(
        entree_configuration, PLATEFORMES_SUPPORTEES
    )

    if dechargement_reussi:
        hass.data[DOMAIN].pop(entree_configuration.entry_id, None)

    return dechargement_reussi
