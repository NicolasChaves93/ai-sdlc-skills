"""Reglas de negocio del sorteo (modelo con «Operación de participantes»): protegen lo que decidió el negocio."""
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "engine"))
from simengine import Model, SimulationTooLong, simulate  # noqa: E402

F = os.path.join(os.path.dirname(__file__), "fixtures")


def rd(n):
    with open(os.path.join(F, n), encoding="utf-8") as fh:
        return fh.read()


FLAT, HIER, SC = rd("sorteo2_flat.bpmn"), rd("sorteo2_hier.bpmn"), json.loads(rd("sorteo2.json"))
n = lambda r, k: r["stats"].get(k, {}).get("entradas", 0)
RUN = lambda p=None, **kw: simulate(FLAT, SC, p or {}, with_samples=False, **kw)


class LoadRules(unittest.TestCase):
    def test_rejected_participants_never_stop_the_draw(self):           # BR-15 / BR-16
        r = RUN({"K": 10, "SORTEOS": 2, "P_RECHAZOS": 1, "P_NINGUNO": 0})
        self.assertEqual(r["ciclo"]["n"], 10)
        self.assertEqual(n(r, "T_Entregar"), 10)                         # el cliente entrega una sola vez: nada lo obliga a repetir
        self.assertEqual(n(r, "T_InfRech"), 10)                          # y a todos se les informó quién y por qué

    def test_only_an_empty_load_blocks_and_the_client_resends(self):    # BR-16
        r = RUN({"K": 6, "SORTEOS": 1, "P_NINGUNO": 0.6}, seed=4)
        self.assertEqual(r["ciclo"]["n"], 6)
        self.assertGreater(n(r, "T_InfNinguno"), 0)
        self.assertEqual(n(r, "T_Entregar"), 6 + n(r, "T_InfNinguno"))   # cada «ninguno» obliga a una nueva entrega
        with self.assertRaises(SimulationTooLong):
            RUN({"K": 1}, forced={"G_Cargo": "F_cargo_no"}, max_case_steps=800)


class OperationRules(unittest.TestCase):
    def test_operations_exist_only_between_rounds(self):                # BR-21: estructura del diagrama por subprocesos
        m = Model(HIER)
        round_inner = {k for k, v in m.container.items() if v == "SP_Sorteo"}
        ops_inner = {k for k, v in m.container.items() if v in ("SP_Operar", "SP_CargarOp")}
        self.assertTrue(round_inner and ops_inner)
        for f in m.flows.values():                                      # nada cruza entre el interior de una ronda y el de una operación
            self.assertFalse(f["source"] in round_inner and f["target"] in ops_inner, f["id"])
            self.assertFalse(f["source"] in ops_inner and f["target"] in round_inner, f["id"])
        into_ops = [m.flows[f]["source"] for f in m.incoming["SP_Operar"]]
        self.assertEqual(into_ops, ["G_Oper"])                           # solo se entra a operar desde la decisión previa a la ronda
        self.assertEqual([m.flows[f]["target"] for f in m.outgoing["SP_Operar"]], ["SP_Sorteo"])   # y al salir se va a la ronda
        self.assertIn("SP_Operar", m.subprocesses)

    def test_all_operations_are_reachable_and_the_draw_still_finishes(self):
        r = RUN({"K": 20, "SORTEOS": 4, "P_RECHAZOS": 1, "P_NINGUNO": 0, "P_MOD": 1, "P_OTRA": 0.5}, seed=3)
        self.assertEqual(r["ciclo"]["n"], 20)
        for step in ("T_SubirOp", "T_ListarP", "T_ListarG", "T_Elegir", "T_Anular", "T_Confirmar", "T_Reiniciar", "T_ReiniciarBase", "T_Corte"):
            self.assertGreater(n(r, step), 0, step)

    def test_deleting_with_winners_always_asks_for_authorization(self):  # BR-19
        r = RUN({"K": 8, "SORTEOS": 3, "P_MOD": 1, "P_RECHAZO": 1, "P_OTRA": 0.5}, seed=2)
        self.assertEqual(n(r, "T_Elim"), 0)                              # con ganadores entre los elegidos nunca se elimina directo
        self.assertGreater(n(r, "T_VerElim"), 0)
        self.assertEqual(n(r, "T_Autorizar"), n(r, "T_VerElim"))
        self.assertEqual(n(r, "T_ElimTodo") + n(r, "T_ElimResto"), n(r, "T_Autorizar"))   # y cada autorización termina en una de las dos opciones
        r2 = RUN({"K": 8, "SORTEOS": 3, "P_MOD": 1, "P_RECHAZO": 0, "P_OTRA": 0.5}, seed=2)
        self.assertEqual(n(r2, "T_Autorizar"), 0)                        # sin ganadores no hace falta autorización
        self.assertEqual(n(r2, "T_Elim"), n(r2, "T_VerElim"))

    def test_both_authorization_options_exist(self):
        p = {"K": 8, "SORTEOS": 3, "P_MOD": 1, "P_RECHAZO": 1, "P_OTRA": 0.5}
        todo = RUN(p, seed=2, forced={"G_Aut": "F_aut_todo"})
        resto = RUN(p, seed=2, forced={"G_Aut": "F_aut_resto"})
        self.assertGreater(n(todo, "T_ElimTodo"), 0)
        self.assertEqual(n(todo, "T_ElimResto"), 0)
        self.assertGreater(n(resto, "T_ElimResto"), 0)
        self.assertEqual(n(resto, "T_ElimTodo"), 0)

    def test_reset_always_asks_for_confirmation(self):                  # BR-22
        r = RUN({"K": 30, "SORTEOS": 4, "P_MOD": 1, "P_OTRA": 0.6}, seed=5)
        self.assertGreater(n(r, "T_Confirmar"), 0)
        self.assertLessEqual(n(r, "T_Reiniciar") + n(r, "T_ReiniciarBase"), n(r, "T_Confirmar"))   # nunca se reinicia sin haber pedido confirmación
        self.assertEqual(n(r, "G_Limpia"), n(r, "T_Reiniciar") + n(r, "T_ReiniciarBase"))        # quien confirma elige qué se limpia: todo o solo la base
        self.assertEqual(n(r, "T_Confirmar"), n(r, "G_Conf"))

    def test_listing_changes_nothing(self):                             # listar es solo consulta: un solo paso y directo al cierre
        m = Model(FLAT)
        for lister in ("T_ListarP", "T_ListarG"):
            self.assertEqual([m.flows[f]["target"] for f in m.outgoing[lister]], ["G_Unir"])


class WinnersNeverRepeat(unittest.TestCase):
    def test_there_is_no_option_to_let_a_winner_win_again(self):        # BR-26: decisión de negocio, no es configurable
        self.assertNotIn("REPETIR", SC["params"])
        self.assertNotIn("T_ConfigSorteo", Model(FLAT).nodes)
        self.assertNotIn("T_ConfigSorteo", Model(HIER).nodes)
        for node in Model(HIER).nodes.values():
            self.assertNotRegex(node["name"].lower(), "repetir ganadores|volver a ganar")

    def test_preparation_starts_with_the_client_delivering_the_base(self):
        h = Model(HIER)
        self.assertEqual([h.flows[f]["target"] for f in h.outgoing["Start_Prep"]], ["T_Entregar"])


class Report(unittest.TestCase):
    def test_report_is_generated_and_delivered_once_after_all_the_rounds(self):     # BR-28
        r = RUN({"K": 5, "SORTEOS": 3, "P_MOD": 1, "P_OTRA": 0.5, "P_NINGUNO": 0.4}, seed=2)
        self.assertEqual(n(r, "T_Reporte"), 5)                           # uno por sorteo, aunque haya reentregas, operaciones o reinicios
        self.assertEqual(n(r, "T_EntregarReporte"), 5)
        m = Model(HIER)
        self.assertEqual([m.flows[f]["source"] for f in m.incoming["T_Reporte"]], ["SP_Sorteos"])   # solo después de terminar todas las rondas
        self.assertEqual([m.flows[f]["target"] for f in m.outgoing["T_Reporte"]], ["T_EntregarReporte"])
        self.assertEqual([m.flows[f]["target"] for f in m.outgoing["T_EntregarReporte"]], ["End_Evento"])

    def test_report_lists_the_agreed_sheets_and_columns(self):
        text = SC["elementos"]["T_Reporte"]["detalle"]
        for sheet in ("Resumen", "Ganadores", "Participantes"):
            self.assertIn(sheet, text)
        for col in ("Grupo sorteo", "Orden en grupo", "Orden general", "Nombre", "Cédula", "Hora", "Ganador real", "Nota"):
            self.assertIn(col, text)
        self.assertNotIn("Orden Preferencial", text)                     # se descartó: solo queda el orden del sorteo


class DrawLoop(unittest.TestCase):
    P = {"K": 5, "SORTEOS": 3, "GANADORES": 2, "P_NINGUNO": 0}

    def test_each_round_finishes_with_exactly_the_requested_real_winners(self):   # BR-24
        r = RUN(self.P, seed=3)
        self.assertEqual(n(r, "T_RegReal"), 5 * 3 * 2)
        self.assertEqual(n(r, "T_RegNoReal"), n(r, "T_Seleccionar") - n(r, "T_RegReal"))      # cada sorteado queda registrado como real o no real (BR-25)
        self.assertGreater(n(r, "T_Seleccionar"), n(r, "T_RegReal"))                       # y hubo que sortear a más personas que ganadores
        self.assertEqual(n(r, "T_Verificar"), n(r, "T_Seleccionar"))                       # a cada sorteado se le verifica antes de decidir

    def test_when_everyone_is_real_nobody_is_discarded(self):
        r = RUN({**self.P, "P_REAL": 1})
        self.assertEqual(n(r, "T_RegNoReal"), 0)
        self.assertEqual(n(r, "T_Seleccionar"), n(r, "T_RegReal"))

    def test_the_number_of_winners_is_per_round_in_both_views(self):
        for g in (1, 3):
            f = RUN({**self.P, "GANADORES": g}, seed=2)
            h = simulate(HIER, SC, {**self.P, "GANADORES": g}, seed=2, with_samples=False)
            self.assertEqual(n(f, "T_RegReal"), 5 * 3 * g)
            self.assertEqual(n(h, "T_RegReal"), 5 * 3 * g)

    def test_never_real_never_ends(self):
        with self.assertRaises(SimulationTooLong):
            RUN({"K": 1, "SORTEOS": 1}, forced={"G_Real": "F_real_no"}, max_case_steps=1500)

    def test_a_discarded_person_goes_back_to_draw_another(self):
        m = Model(HIER)
        tgt = lambda node: sorted(m.flows[f]["target"] for f in m.outgoing[node])
        self.assertEqual(tgt("T_Mostrar"), ["T_Verificar"])
        self.assertEqual(tgt("T_Verificar"), ["G_Real"])
        self.assertEqual(tgt("T_RegNoReal"), ["T_Seleccionar"])                            # no real: se sortea otra persona
        self.assertEqual(sorted(tgt("G_Faltan")), ["End_Sorteo", "T_Seleccionar"])          # real: se sigue solo si faltan ganadores


class IdAndEnableRules(unittest.TestCase):
    def test_a_missing_id_never_blocks_the_load(self):                  # BR-18
        a = RUN({"K": 6, "SORTEOS": 2, "P_NINGUNO": 0, "P_SINID": 1, "P_MOD": 1, "P_OTRA": 0.5}, seed=2)
        self.assertEqual(a["ciclo"]["n"], 6)
        self.assertEqual(n(a, "T_AsignarId"), n(a, "T_Validar"))          # en toda carga inicial, quien no trae id recibe uno único
        self.assertEqual(n(a, "T_AsignarIdOp"), n(a, "T_ValidarOp"))      # y también al cargar durante el evento
        b = RUN({"K": 6, "SORTEOS": 2, "P_NINGUNO": 0, "P_SINID": 0, "P_MOD": 1, "P_OTRA": 0.5}, seed=2)
        self.assertEqual(n(b, "T_AsignarId") + n(b, "T_AsignarIdOp"), 0)
        self.assertEqual(n(a, "T_Entregar"), n(b, "T_Entregar"))          # no provoca que el cliente vuelva a entregar la base

    def test_enabling_again_is_optional_and_happens_before_checking_who_is_eligible(self):   # BR-26
        on = RUN({"K": 5, "SORTEOS": 3, "P_HAB": 1, "P_NOALCANZA": 0}, seed=1)
        off = RUN({"K": 5, "SORTEOS": 3, "P_HAB": 0, "P_NOALCANZA": 0}, seed=1)
        self.assertEqual(n(on, "T_Habilitar"), 5 * 3)                    # uno por sorteo, solo si se decide
        self.assertEqual(n(off, "T_Habilitar"), 0)
        self.assertEqual(n(on, "T_RegReal"), n(off, "T_RegReal"))         # habilitar no cambia cuántos ganadores reales se buscan
        m = Model(HIER)
        tgt = lambda node: sorted(m.flows[f]["target"] for f in m.outgoing[node])
        self.assertEqual(tgt("T_Config"), ["G_Hab"])
        self.assertEqual(tgt("T_Habilitar"), ["G_UneHab"])
        self.assertEqual(tgt("G_UneHab"), ["G_Alcanza"])

    def test_only_those_who_were_not_real_winners_can_be_enabled(self):  # BR-26: un ganador real nunca se habilita
        m = Model(HIER)
        for node in ("G_Hab", "T_Habilitar"):
            self.assertIn("no fueron ganador real", m.nodes[node]["name"])
        self.assertIn("nunca", SC["elementos"]["T_Habilitar"]["detalle"])
        self.assertIn("ganador real nunca", SC["elementos"]["G_Hab"]["detalle"].lower())


class Vocabulary(unittest.TestCase):
    def test_an_event_contains_several_sorteos_and_nothing_is_called_ronda(self):
        m = Model(HIER)
        self.assertIn("Evento", m.nodes["Start_Evento"]["name"] + m.nodes["End_Evento"]["name"])
        self.assertEqual(m.nodes["SP_Sorteos"]["name"], "2. Sorteos del evento")
        self.assertEqual(m.nodes["SP_Sorteo"]["name"], "Sorteo general")
        for k, v in m.nodes.items():
            self.assertNotRegex((k + " " + v["name"]).lower(), "ronda", k)
        text = json.dumps(SC, ensure_ascii=False).lower()
        self.assertNotIn("ronda", text)
        self.assertIn("SORTEOS", SC["params"])
        self.assertNotIn("RONDAS", SC["params"])


class Movement(unittest.TestCase):
    def test_every_arrow_is_recorded_in_both_views(self):
        mf, mh = Model(FLAT), Model(HIER)
        flat = simulate(FLAT, SC, {"K": 3, "SORTEOS": 3}, mode="peor", with_samples=False)
        hier = simulate(HIER, SC, {"K": 3, "SORTEOS": 3}, mode="peor", with_samples=False)
        pair = lambda m, f: (m.flows[f]["source"], m.flows[f]["target"])
        flat_by_pair = {pair(mf, f): c for f, c in flat["flowCount"].items()}
        shared = 0
        for f, c in hier["flowCount"].items():              # misma flecha (mismo origen y destino) = mismo número de recorridos
            if pair(mh, f) in flat_by_pair:
                self.assertEqual(c, flat_by_pair[pair(mh, f)], f)
                shared += 1
        self.assertGreaterEqual(shared, 15)
        for shell_flow in ("F_s2", "F_oper_si", "F_oper_fin", "F_op_cargar", "F_x1", "F_x2"):   # flechas hacia/desde subprocesos: solo existen en la vista por subprocesos
            self.assertGreater(hier["flowCount"].get(shell_flow, 0), 0, shell_flow)
        self.assertEqual(hier["flowCount"]["F_x1"], 3)
        self.assertEqual(hier["flowCount"]["F_op_cargar"], hier["stats"]["SP_CargarOp"]["entradas"])


class Modes(unittest.TestCase):
    def test_best_and_worst_case_and_diagram_views_agree(self):
        mejor, peor = RUN({"K": 3, "SORTEOS": 3}, mode="mejor"), RUN({"K": 3, "SORTEOS": 3}, mode="peor")
        for k in ("T_InfNinguno", "T_SubirOp", "G_Op", "T_Autorizar"):
            self.assertEqual(n(mejor, k), 0, k)
        self.assertEqual(n(peor, "T_InfNinguno"), 3 * 2)
        self.assertGreater(peor["ciclo"]["prom"], mejor["ciclo"]["prom"] * 3)
        h = simulate(HIER, SC, {"K": 3, "SORTEOS": 3}, mode="peor", with_samples=False)
        for k in ("T_InfNinguno", "T_SubirOp", "T_Autorizar", "T_Ajustar", "T_Seleccionar", "G_Op"):
            self.assertEqual(n(peor, k), n(h, k), k)
        self.assertEqual(h["stats"]["SP_Operar"]["entradas"], 3 * 3)     # 3 sorteos x 3 rondas operando antes de cada una


if __name__ == "__main__":
    unittest.main()
