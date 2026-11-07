"""Flux de configuration sécurisé pour l'intégration EVO-START."""
from typing import Any
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import DOMAIN
from .coordinator import CoordinateurEvoStart


async def valider_authentification_distante(
    hass: HomeAssistant, donnees: dict[str, Any]
) -> None:
    """Tester la validité des identifiants auprès de l'API distante."""
    coordinateur_test = CoordinateurEvoStart(
        hass,
        courriel=donnees[CONF_EMAIL],
        mot_de_passe=donnees[CONF_PASSWORD],
    )
    succes = await coordinateur_test.authentifier()
    if not succes:
        raise ErreurAuthentificationInvalide


class FluxConfigurationEvoStart(config_entries.ConfigFlow, domain=DOMAIN):
    """Gestionnaire du flux de configuration avec protection contre les doublons."""

    VERSION = 1

    async def async_step_user(
        self, entrees_utilisateur: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Traiter la saisie utilisateur et enregistrer l'intégration."""
        erreurs: dict[str, str] = {}

        if entrees_utilisateur is not None:
            courriel_normalise = entrees_utilisateur[CONF_EMAIL].strip().lower()

            # Bloquer l'ajout multiple du même compte
            await self.async_set_unique_id(courriel_normalise)
            self._abort_if_unique_id_configured()

            try:
                await valider_authentification_distante(self.hass, entrees_utilisateur)
            except ErreurAuthentificationInvalide:
                erreurs["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                erreurs["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title=f"EVO-START ({courriel_normalise})",
                    data={
                        CONF_EMAIL: courriel_normalise,
                        CONF_PASSWORD: entrees_utilisateur[CONF_PASSWORD],
                    },
                )

        schema_formulaire = vol.Schema(
            {
                vol.Required(CONF_EMAIL): TextSelector(
                    TextSelectorConfig(
                        type=TextSelectorType.EMAIL,
                        autocomplete="email",
                    )
                ),
                vol.Required(CONF_PASSWORD): TextSelector(
                    TextSelectorConfig(
                        type=TextSelectorType.PASSWORD,
                        autocomplete="current-password",
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema_formulaire,
            errors=erreurs,
        )


class ErreurAuthentificationInvalide(HomeAssistantError):
    """Exception levée lorsque le serveur rejette les identifiants."""


# Alias pour maintenir la compatibilité descendante avec Home Assistant
EvoStartConfigFlow = FluxConfigurationEvoStart
