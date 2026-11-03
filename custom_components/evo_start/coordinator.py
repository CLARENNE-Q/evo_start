"""Coordinateur de données sécurisé avec intégration des trajets et odomètre persistant pour EVO-START."""
import os
import json
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Any

from aiohttp import ClientError, ClientTimeout
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

JOURNALISEUR = logging.getLogger(__name__)

URL_POINT_ENTREE = "https://shk.topm2m.net/webinv/do&req_seq={seq}"
EN_TETES_REQUETE = {
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "X-Requested-With": "XMLHttpRequest",
}
DELAI_EXPIRATION_SECONDES = 15

CHAMPS_BINAIRES = {
    "lig_smal": 1, "lig_big": 2, "dor_frn": 3, "dor_trk": 4, "dor_rb": 5,
    "dor_rf": 6, "dor_lb": 7, "dor_lf": 8, "vcl_on2": 9, "vcl_on1": 10,
    "wnd_top": 12, "wnd_rb": 13, "wnd_rf": 14, "wnd_lb": 15, "vcl_anit": 16,
    "vcl_repair": 18, "vcl_lok": 19, "vcl_eng": 20, "vcl_acc": 21, "vcl_air": 22,
    "brk_fot": 23, "brk_han": 24, "gps_cls": 29, "gps_opn": 30, "gps_loc": 31,
    "gps_power": 32, "alm_tpms": 33, "alm_bat": 34, "alm_belt_m": 35,
    "alm_acc": 36, "alm_dor": 37, "alm_vib": 38, "alm_ultrasonic": 39,
    "alm_dor_open": 40,
}

DRAPEAUX_INVERSES = set()


class CoordinateurEvoStart(DataUpdateCoordinator[dict[str, Any]]):
    """Gestionnaire centralisé des requêtes réseau et du cycle de vie des sessions."""

    def __init__(self, hass: HomeAssistant, courriel: str, mot_de_passe: str) -> None:
        super().__init__(
            hass,
            JOURNALISEUR,
            name=DOMAIN,
            update_interval=timedelta(seconds=60),
        )
        self.session_client = async_get_clientsession(hass)
        self.courriel = courriel.strip().lower()
        self.mot_de_passe_hache = self._calculer_sha1(mot_de_passe)
        self.identifiant_utilisateur: str | None = None
        self.jeton_session: str | None = None
        self.vehicles_data: dict[str, Any] = {}
        self.vehicles_flags: dict[str, Any] = {}
        self.vehicles_trips: dict[str, Any] = {}

    @staticmethod
    def _calculer_sha1(chaine: str) -> str:
        return hashlib.sha1(chaine.encode("utf-8")).hexdigest().upper()

    def _charger_odometre_disque(self, tid: str) -> dict[str, Any]:
        chemin = self.hass.config.path("evo_start_odometer.json")
        try:
            if os.path.exists(chemin):
                with open(chemin, "r", encoding="utf-8") as f:
                    donnees = json.load(f)
                    if tid in donnees:
                        return donnees[tid]
        except Exception as err:
            JOURNALISEUR.warning("Erreur lecture odomètre persistant: %s", err)

        donnees_defaut = {
            "odometre_km": 0.0,
            "dernier_ts_traite": 0,
        }
        self._sauvegarder_odometre_disque(tid, donnees_defaut["odometre_km"], donnees_defaut["dernier_ts_traite"])
        return donnees_defaut

    def _sauvegarder_odometre_disque(self, tid: str, odometre_km: float, dernier_ts: int) -> None:
        chemin = self.hass.config.path("evo_start_odometer.json")
        try:
            toutes_donnees = {}
            if os.path.exists(chemin):
                with open(chemin, "r", encoding="utf-8") as f:
                    try:
                        toutes_donnees = json.load(f)
                    except Exception:
                        toutes_donnees = {}
            toutes_donnees[tid] = {
                "odometre_km": round(odometre_km, 2),
                "dernier_ts_traite": dernier_ts,
                "derniere_mise_a_jour": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            with open(chemin, "w", encoding="utf-8") as f:
                json.dump(toutes_donnees, f, indent=2, ensure_ascii=False)
        except Exception as err:
            JOURNALISEUR.error("Erreur écriture odomètre persistant: %s", err)

    def _construire_charge_utile(
        self,
        code_operation: str,
        identifiant: str | None = None,
        jeton: str | None = None,
        identifiant_terminal: str | None = None,
        corps_personnalise: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        horodatage = datetime.now()
        estampille = horodatage.strftime("%y%m%d%H%M%S")
        identifiant_resolu = identifiant or "00000000"

        charge = {
            "sys_head": {
                "ver": "1.0",
                "code": code_operation,
                "consumer_ssn": f"{identifiant_resolu}{estampille}0142",
                "trans_date": horodatage.strftime("%Y%m%d"),
                "trans_time": horodatage.strftime("%H%M%S"),
                "chnl": "android",
                "build_make": "Google",
                "aver": "2.1.00",
                "build_model": "Pixel 10 Pro XL",
                "build_release": "17",
                "distribute": "evostart",
            },
            "app_head": {
                "uid": identifiant_resolu,
                "ssk": jeton,
                "chnl": "android",
                "lang": "fr",
                "timezone": "-18000",
            },
            "body": {} if not identifiant_terminal else {"tid": identifiant_terminal},
        }
        if corps_personnalise is not None:
            charge["body"] = corps_personnalise
        return charge

    async def _envoyer_requete_securisee(self, charge_utile: dict[str, Any]) -> dict[str, Any]:
        horodatage_ms = str(int(datetime.now().timestamp() * 1000))
        url_cible = URL_POINT_ENTREE.format(seq=horodatage_ms)
        delai = ClientTimeout(total=DELAI_EXPIRATION_SECONDES)

        try:
            async with self.session_client.post(
                url_cible,
                headers=EN_TETES_REQUETE,
                data=json.dumps(charge_utile),
                timeout=delai,
                ssl=True,
            ) as reponse:
                if reponse.status != 200:
                    raise UpdateFailed(f"Erreur HTTP: {reponse.status}")
                return await reponse.json(content_type=None)
        except ClientError as exception_reseau:
            raise UpdateFailed(f"Erreur réseau: {exception_reseau}") from exception_reseau

    async def authentifier(self) -> bool:
        charge_utile = self._construire_charge_utile("100010")
        charge_utile["body"] = {
            "name": self.courriel,
            "paswd": self.mot_de_passe_hache,
        }
        donnees = await self._envoyer_requete_securisee(charge_utile)
        if donnees.get("sys_head", {}).get("ret_code") == "000000":
            corps = donnees.get("body", {})
            self.identifiant_utilisateur = corps.get("uid")
            self.jeton_session = corps.get("ssk")
            return True
        self.jeton_session = None
        return False

    async def _recuperer_trajets_jour(self, tid: str) -> dict[str, Any]:
        maintenant = datetime.now()
        debut_mois = maintenant.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        ts_debut = str(int(debut_mois.timestamp()))
        ts_fin = str(int(maintenant.timestamp()))

        charge_trajets = self._construire_charge_utile(
            code_operation="901010",
            identifiant=self.identifiant_utilisateur,
            jeton=self.jeton_session,
            corps_personnalise={
                "mode": "10",
                "bgdt": ts_debut,
                "eddt": ts_fin,
                "tid": tid,
            },
        )
        reponse = await self._envoyer_requete_securisee(charge_trajets)
        lignes = reponse.get("body", {}).get("rows", [])

        donnees_odo = await self.hass.async_add_executor_job(self._charger_odometre_disque, tid)
        odometre_km = float(donnees_odo.get("odometre_km", 0.0))
        dernier_ts = int(donnees_odo.get("dernier_ts_traite", 0))

        lignes_triees = sorted(lignes, key=lambda x: int(x.get("edtdt", 0)))
        nouveaux_km = 0.0
        nouveau_dernier_ts = dernier_ts

        for viaje in lignes_triees:
            ts_fin_viaje = int(viaje.get("edtdt", 0))
            if ts_fin_viaje > dernier_ts:
                metros = int(viaje.get("trip", 0))
                if metros > 0:
                    km = round(metros / 1000.0, 2)
                    nouveaux_km += km
                    JOURNALISEUR.info("Nouveau trajet détecté: +%s km", km)
                nouveau_dernier_ts = ts_fin_viaje

        if nouveau_dernier_ts > dernier_ts or nouveaux_km > 0:
            odometre_km = round(odometre_km + nouveaux_km, 2)
            await self.hass.async_add_executor_job(
                self._sauvegarder_odometre_disque, tid, odometre_km, nouveau_dernier_ts
            )

        debut_journee_ts = int(maintenant.replace(hour=0, minute=0, second=0, microsecond=0).timestamp())
        trajets_aujourdhui = [v for v in lignes if int(v.get("bgtdt", 0)) >= debut_journee_ts]
        distance_aujourdhui_m = sum(int(v.get("trip", 0)) for v in trajets_aujourdhui)

        distance_mois_m = sum(int(v.get("trip", 0)) for v in lignes)
        dernier_voyage = lignes_triees[-1] if lignes_triees else {}

        return {
            "odometre_km": round(odometre_km, 1),
            "distance_jour_km": round(distance_aujourdhui_m / 1000.0, 2),
            "distance_mois_km": round(distance_mois_m / 1000.0, 1),
            "nombre_trajets_jour": len(trajets_aujourdhui),
            "dernier_trajet_km": round(int(dernier_voyage.get("trip", 0)) / 1000.0, 2),
            "dernier_trajet_vitesse_max": int(dernier_voyage.get("top", 0)),
        }

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            if not self.jeton_session or not self.identifiant_utilisateur:
                if not await self.authentifier():
                    raise UpdateFailed("Authentification initiale impossible")

            charge_utile = self._construire_charge_utile(
                "20101010",
                identifiant=self.identifiant_utilisateur,
                jeton=self.jeton_session,
            )
            donnees_reponse = await self._envoyer_requete_securisee(charge_utile)

            if donnees_reponse.get("sys_head", {}).get("ret_code") != "000000":
                if not await self.authentifier():
                    raise UpdateFailed("Renouvellement de session rejeté")
                charge_utile = self._construire_charge_utile(
                    "20101010",
                    identifiant=self.identifiant_utilisateur,
                    jeton=self.jeton_session,
                )
                donnees_reponse = await self._envoyer_requete_securisee(charge_utile)

            liste_vehicules = donnees_reponse.get("body", {}).get("rows", [])
            donnees_consolidees = {}
            drapeaux_consolides = {}
            trajets_consolides = {}

            for element in liste_vehicules:
                tid = element.get("tid")
                charge_loc = element.get("lloc", {})
                drapeaux_consolides[tid] = self.decoder_chaine_vst(charge_loc.get("vst", ""))
                donnees_consolidees[tid] = {
                    "lloc": charge_loc,
                    "carinfo": element.get("carinfo", {}),
                    "tid": tid,
                }
                try:
                    trajets_consolides[tid] = await self._recuperer_trajets_jour(tid)
                except Exception as e:
                    JOURNALISEUR.debug("Erreur lors de la lecture des trajets: %s", e)
                    odo_precedent = self.vehicles_trips.get(tid, {}).get("odometre_km", 0.0)
                    trajets_consolides[tid] = self.vehicles_trips.get(tid, {
                        "odometre_km": odo_precedent,
                        "distance_jour_km": 0.0,
                        "distance_mois_km": 0.0,
                        "nombre_trajets_jour": 0,
                        "dernier_trajet_km": 0.0,
                        "dernier_trajet_vitesse_max": 0,
                    })

            self.vehicles_data = donnees_consolidees
            self.vehicles_flags = drapeaux_consolides
            self.vehicles_trips = trajets_consolides

            return {
                "vehicles": donnees_consolidees,
                "flags": drapeaux_consolides,
                "trips": trajets_consolides,
            }
        except Exception as anomalie:
            raise UpdateFailed(f"Anomalie durant l'actualisation: {anomalie}") from anomalie

    def decoder_chaine_vst(self, sequence_vst: str) -> dict[str, str | None]:
        if not sequence_vst:
            return {}
        segment_hexa = sequence_vst[:10]
        representation_binaire = bin(int("1" + segment_hexa, 16))[2:].zfill(41)
        resultats = {}
        for cle_capteur, position_bit in CHAMPS_BINAIRES.items():
            if position_bit >= len(representation_binaire):
                resultats[cle_capteur] = None
            else:
                valeur_bit = representation_binaire[position_bit]
                if cle_capteur in DRAPEAUX_INVERSES:
                    valeur_bit = "0" if valeur_bit == "1" else "1"
                resultats[cle_capteur] = valeur_bit
        return resultats

    def get_vehicle_data(self, vehicle_id: str) -> dict[str, Any] | None:
        return self.vehicles_data.get(vehicle_id)

    def get_vehicle_flags(self, vehicle_id: str) -> dict[str, Any]:
        return self.vehicles_flags.get(vehicle_id, {})

    def get_vehicle_trips(self, vehicle_id: str) -> dict[str, Any]:
        return self.vehicles_trips.get(vehicle_id, {})

    def get_all_vehicle_ids(self) -> list[str]:
        return list(self.vehicles_data.keys())

    async def _executer_commande_actionneur(self, code_action: str, tid: str) -> bool:
        if not self.jeton_session and not await self.authentifier():
            return False
        charge = self._construire_charge_utile(
            code_action,
            identifiant=self.identifiant_utilisateur,
            jeton=self.jeton_session,
            identifiant_terminal=tid,
        )
        rep = await self._envoyer_requete_securisee(charge)
        return rep.get("sys_head", {}).get("ret_code") == "000000"

    async def async_remote_start(self, vehicle_id: str) -> bool:
        return await self._executer_commande_actionneur("303120", vehicle_id)

    async def async_remote_stop(self, vehicle_id: str) -> bool:
        return await self._executer_commande_actionneur("303125", vehicle_id)

    async def async_remote_lock(self, vehicle_id: str) -> bool:
        return await self._executer_commande_actionneur("303110", vehicle_id)

    async def async_remote_unlock(self, vehicle_id: str) -> bool:
        return await self._executer_commande_actionneur("303115", vehicle_id)


# Alias pour la compatibilité ascendante
EvoStartCoordinator = CoordinateurEvoStart
