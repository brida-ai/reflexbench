#!/usr/bin/env python3
"""Build the blind Core-v1 workflow case pack after the procedure was frozen.

No engine/model output is consumed. Each scenario is authored once and rendered as a
paired EN/ES case with the expected operational branch fixed before inference.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

PROCEDURE_COMMIT = "e4f171401"
EVIDENCE_CLASS = "blind_synthetic_workflow"


def bi(en: Any, es: Any) -> dict[str, Any]:
    return {"en": en, "es": es}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def render_value(value: Any, language: str) -> Any:
    if isinstance(value, dict) and set(value) == {"en", "es"}:
        return value[language]
    return value


def make_case(
    workflow: str,
    index: int,
    case_class: str,
    expected: str,
    state: dict[str, Any],
    language: str,
) -> dict[str, Any]:
    return {
        "id": f"{workflow}-blind-{index:02d}-{language}",
        "useCase": workflow,
        "language": language,
        "caseClass": case_class,
        "evidenceClass": EVIDENCE_CLASS,
        "state": {k: render_value(v, language) for k, v in state.items()},
        "expectedBranch": expected,
        "provenance": {
            "authoring": "pre-inference deterministic scenario matrix",
            "procedureCommit": PROCEDURE_COMMIT,
            "modelOutputsObservedBeforeFreeze": False,
            "pairedTranslationGroup": f"{workflow}-blind-{index:02d}",
        },
    }


def sales() -> list[tuple[str, str, dict[str, Any]]]:
    icp = bi(
        "B2B software company with 20-200 employees and repetitive support or operations triage",
        "Empresa de software B2B con 20-200 empleados y triaje repetitivo de soporte u operaciones",
    )
    def s(cls, expected, company, employees, company_type_en, company_type_es, use_en, use_es):
        return (
            cls,
            expected,
            {
                "icp": icp,
                "company": company,
                "employeeCount": employees,
                "companyType": bi(company_type_en, company_type_es),
                "useCase": bi(use_en, use_es),
            },
        )
    return [
        s("clear", "qualified", "Support Cloud", 65, "B2B SaaS", "SaaS B2B", "Route repetitive inbound support tickets before human escalation", "Clasificar tickets repetitivos de soporte antes de escalar a una persona"),
        s("clear", "qualified", "Helpdesk Metrics", 140, "B2B software", "Software B2B", "Triage repeated customer incidents into support queues", "Clasificar incidentes repetidos de clientes en colas de soporte"),
        s("clear", "qualified", "Ops Relay", 35, "B2B SaaS", "SaaS B2B", "Route repetitive operations alerts before waking an on-call agent", "Clasificar alertas operativas repetitivas antes de avisar al equipo de guardia"),
        s("clear", "ignore", "Weekend Photo Club", 5, "consumer photography studio", "estudio de fotografía de consumo", "Generate artistic social captions", "Generar textos creativos para redes sociales"),
        s("clear", "ignore", "Mass Media World", 5000, "consumer media group", "grupo de medios de consumo", "Generate movie trailer concepts", "Generar conceptos para tráilers de películas"),
        s("boundary", "review", "Tiny Supportware", 18, "B2B software", "Software B2B", "Route a high volume of repetitive support tickets", "Clasificar un alto volumen de tickets de soporte repetitivos"),
        s("boundary", "review", "Scale Desk", 205, "B2B SaaS", "SaaS B2B", "Automate first-pass support triage", "Automatizar el primer triaje de soporte"),
        s("boundary", "review", "Board Notes AI", 80, "B2B software", "Software B2B", "Summarize quarterly board notes, not support messages", "Resumir notas trimestrales del consejo, no mensajes de soporte"),
        s("boundary", "review", "SaaS Service Agency", 55, "agency serving several software clients", "agencia que atiende a varios clientes de software", "Share one triage queue across client support inboxes", "Compartir una cola de triaje entre bandejas de soporte de clientes"),
        s("boundary", "review", "Experiment Labs", 120, "B2B software", "Software B2B", "Exploring AI for internal workflows; no specific repetitive triage selected yet", "Explorando IA para flujos internos; aún sin un triaje repetitivo concreto"),
        s("ambiguous", "review", "Platform Unknown", None, "software platform; market not stated", "plataforma de software; mercado no indicado", "Route inbound messages, but the message type and volume are not described", "Clasificar mensajes entrantes, pero no se describe el tipo ni el volumen"),
        s("ambiguous", "review", "Mixed Marketplace", 60, "marketplace serving businesses and consumers", "marketplace que atiende a empresas y consumidores", "Categorize chat conversations before agents read them", "Categorizar conversaciones de chat antes de que las lean agentes"),
        s("ambiguous", "review", "Dev Consulting Co", 25, "consulting firm that builds software for clients", "consultora que desarrolla software para clientes", "Triage client email requests across projects", "Clasificar solicitudes por correo de clientes entre proyectos"),
        s("ambiguous", "review", "Enterprise Spinout", 190, "software subsidiary inside a larger consumer group", "filial de software dentro de un grupo de consumo mayor", "Mix of support routing and marketing-message classification", "Mezcla de enrutamiento de soporte y clasificación de mensajes de marketing"),
        s("ambiguous", "review", "Reply Assist", 70, "B2B SaaS", "SaaS B2B", "Generate personalized replies to support requests; routing is only a possible future step", "Generar respuestas personalizadas a solicitudes de soporte; el enrutamiento sería un paso futuro"),
    ]


def support() -> list[tuple[str, str, dict[str, Any]]]:
    def s(cls, expected, area, summary_en, summary_es, impact_en, impact_es, urgency_en, urgency_es, known=None):
        state = {
            "productArea": area,
            "summary": bi(summary_en, summary_es),
            "customerImpact": bi(impact_en, impact_es),
            "urgency": bi(urgency_en, urgency_es),
        }
        if known is not None:
            state["knownResolution"] = bi(known[0], known[1])
        return cls, expected, state
    return [
        s("clear", "escalate", "checkout", "All checkout attempts fail after the latest deploy.", "Todos los intentos de pago fallan desde el último despliegue.", "No orders can be processed.", "No se puede procesar ningún pedido.", "high", "alta"),
        s("clear", "escalate", "api", "A customer reports exposed production API credentials in a public log.", "Un cliente reporta credenciales de API de producción expuestas en un registro público.", "Potential unauthorized access.", "Posible acceso no autorizado.", "high", "alta"),
        s("clear", "self_serve", "profile", "Where can I change the display name?", "¿Dónde puedo cambiar el nombre visible?", "Informational request.", "Solicitud informativa.", "low", "baja", ("Settings > Profile > Display name", "Configuración > Perfil > Nombre visible")),
        s("clear", "queue", "billing", "Please send a copy of last month’s paid invoice.", "Por favor envíen una copia de la factura pagada del mes pasado.", "Administrative request; service works normally.", "Solicitud administrativa; el servicio funciona con normalidad.", "normal", "normal"),
        s("clear", "queue", "notifications", "One user cannot save notification preferences.", "Un usuario no puede guardar sus preferencias de notificación.", "Single user; workaround is available.", "Un solo usuario; existe una alternativa temporal.", "normal", "normal"),
        s("boundary", "review", "checkout", "Two of roughly twenty checkout attempts failed this morning.", "Dos de unos veinte intentos de pago fallaron esta mañana.", "Some orders may be delayed; scope is still being checked.", "Algunos pedidos podrían retrasarse; aún se revisa el alcance.", "medium", "media"),
        s("boundary", "review", "payments", "A single customer says every card is declined and calls it urgent.", "Un solo cliente dice que todas sus tarjetas son rechazadas y lo considera urgente.", "Impact beyond that account is unknown.", "Se desconoce si afecta a más cuentas.", "high", "alta"),
        s("boundary", "review", "login", "Password reset instructions are known, but the reset link loops back to sign-in.", "Se conocen las instrucciones para restablecer la contraseña, pero el enlace vuelve al inicio de sesión.", "Could be documentation or product failure.", "Podría ser documentación o un fallo del producto.", "normal", "normal", ("Use the password reset email link.", "Usar el enlace del correo de restablecimiento.")),
        s("boundary", "review", "security", "Customer asks whether a suspicious email is really from us; no headers or links were provided.", "El cliente pregunta si un correo sospechoso es realmente nuestro; no aportó cabeceras ni enlaces.", "No confirmed compromise.", "No hay compromiso confirmado.", "medium", "media"),
        s("boundary", "review", "dashboard", "Dashboard became slow after a deploy for one team. Other teams have not reported it.", "El panel se volvió lento tras un despliegue para un equipo. Otros equipos no lo han reportado.", "Work continues but with delay.", "El trabajo continúa, aunque con retraso.", "medium", "media"),
        s("ambiguous", "review", "unknown", "Nothing works. Please help.", "Nada funciona. Ayuda, por favor.", "Not described.", "No descrito.", "not stated", "no indicada"),
        s("ambiguous", "review", "unknown", "URGENT — need this fixed today.", "URGENTE — necesito que esto se arregle hoy.", "No issue details or impact supplied.", "No se aportan detalles del problema ni del impacto.", "high", "alta"),
        s("ambiguous", "review", "security", "Is this a security problem? I saw something odd.", "¿Esto es un problema de seguridad? Vi algo raro.", "No concrete event described.", "No se describe ningún evento concreto.", "not stated", "no indicada"),
        s("ambiguous", "review", "billing", "Where is my invoice? Also, payments sometimes fail.", "¿Dónde está mi factura? Además, a veces fallan los pagos.", "Mixed informational and failure report; scope unknown.", "Mezcla de consulta informativa y fallo; alcance desconocido.", "not stated", "no indicada"),
        s("ambiguous", "review", "profile", "The help article says to use Profile settings, but my screen looks different.", "El artículo de ayuda dice que use la configuración del perfil, pero mi pantalla es distinta.", "Unable to tell whether this is documentation drift or an account-specific issue.", "No se puede determinar si es documentación desactualizada o un problema específico de la cuenta.", "low", "baja", ("Settings > Profile", "Configuración > Perfil")),
    ]


def issues() -> list[tuple[str, str, dict[str, Any]]]:
    def s(cls, expected, title_en, title_es, body_en, body_es, complete, duplicate, repro):
        return (
            cls,
            expected,
            {
                "title": bi(title_en, title_es),
                "body": bi(body_en, body_es),
                "repositoryContext": bi("software repository", "repositorio de software"),
                "deterministicSignals": {
                    "templateComplete": complete,
                    "exactDuplicateFound": duplicate,
                    "protectedSecurityReport": False,
                    "reproducibleEvidencePresent": repro,
                },
            },
        )
    return [
        s("clear", "investigate_candidate", "Parser crashes on empty optional section", "El parser falla con una sección opcional vacía", "Version 4.2.1 throws at the same stack location; minimal input and clean-install reproduction are included.", "La versión 4.2.1 falla en el mismo punto de la pila; se incluyen entrada mínima y reproducción en instalación limpia.", True, False, True),
        s("clear", "ask_author_candidate", "Export does not work", "La exportación no funciona", "It stopped working for me. No version, steps or error are included.", "Dejó de funcionar. No se incluye versión, pasos ni error.", False, False, False),
        s("clear", "decision_review", "Allow custom retention periods", "Permitir periodos de retención personalizados", "Add an organization setting for owners to choose 30–365 day retention; this changes current product policy.", "Añadir una opción para que propietarios elijan retención de 30–365 días; cambia la política actual del producto.", True, False, False),
        s("clear", "backlog_candidate", "Fix typo in configuration guide", "Corregir errata en la guía de configuración", "The setup guide has a typo; exact file and line are supplied.", "La guía tiene una errata; se indican archivo y línea exactos.", True, False, True),
        s("clear", "close_review", "Same crash as issue #412", "Mismo fallo que el issue #412", "This report reproduces the exact stack trace already tracked in #412; duplicate link is supplied.", "Este reporte reproduce exactamente la traza ya registrada en #412; se aporta el enlace al duplicado.", True, True, True),
        s("boundary", "human_triage", "Save sometimes fails after editing", "A veces falla guardar tras editar", "Steps are listed, but expected behavior and affected version are missing; one screenshot suggests an error.", "Se listan pasos, pero faltan el comportamiento esperado y la versión afectada; una captura sugiere un error.", False, False, True),
        s("boundary", "human_triage", "Current workflow should auto-archive", "El flujo actual debería archivar automáticamente", "Reporter calls it a bug, but requested auto-archive behavior is not documented as existing functionality.", "El autor lo llama bug, pero el archivado automático solicitado no está documentado como funcionalidad existente.", True, False, False),
        s("boundary", "human_triage", "Update dependency to latest major", "Actualizar dependencia a la última versión mayor", "Requests a major dependency bump and mentions security generally, but supplies no advisory or affected-version evidence.", "Solicita una actualización mayor y menciona seguridad en general, pero no aporta aviso ni evidencia de versiones afectadas.", True, False, False),
        s("boundary", "human_triage", "How should reconnect behave?", "¿Cómo debería comportarse la reconexión?", "Asks a usage question but also describes one intermittent disconnect; no minimal reproduction is included.", "Hace una pregunta de uso pero también describe una desconexión intermitente; no incluye reproducción mínima.", False, False, False),
        s("boundary", "human_triage", "Unsupported OS maybe closes immediately", "Sistema no soportado quizá se cierra enseguida", "Report is from an OS not listed in docs, but support policy does not say whether reports should be closed.", "El reporte proviene de un SO no listado, pero la política no indica si debe cerrarse.", True, False, True),
        s("ambiguous", "human_triage", "Sync is weird", "La sincronización está rara", "Sometimes it is weird after I open the app.", "A veces se comporta raro después de abrir la aplicación.", False, False, False),
        s("ambiguous", "human_triage", "Import bug plus new mapping option", "Bug de importación y nueva opción de mapeo", "One paragraph reports wrong imported values; another asks for a new custom mapping feature.", "Un párrafo reporta valores importados incorrectos; otro solicita una nueva función de mapeo personalizado.", False, False, False),
        s("ambiguous", "human_triage", "Trace attached", "Traza adjunta", "A stack trace is pasted with no version, input, expected behavior or steps.", "Se pega una traza sin versión, entrada, comportamiento esperado ni pasos.", False, False, True),
        s("ambiguous", "human_triage", "Does feature X work or is this broken?", "¿Funciona la función X o está rota?", "Reporter cannot tell whether a missing control is unsupported behavior or a defect; docs are not cited.", "El autor no sabe si un control ausente es comportamiento no soportado o un defecto; no cita documentación.", False, False, False),
        s("ambiguous", "human_triage", "Maybe duplicate of an old issue", "Quizá duplicado de un issue antiguo", "Reporter remembers a similar issue but gives no issue number, link or matching stack trace.", "El autor recuerda un issue parecido pero no da número, enlace ni traza coincidente.", False, False, False),
    ]


def content_quality() -> list[tuple[str, str, dict[str, Any]]]:
    facts = bi(
        ["Free Preview", "No card required", "Recommendation only"],
        ["Vista previa gratuita", "No requiere tarjeta", "Solo recomendación"],
    )
    def s(cls, expected, draft_en, draft_es, required=None):
        return (
            cls,
            expected,
            {
                "audience": bi("New users", "Usuarios nuevos"),
                "requiredFacts": facts if required is None else required,
                "draft": bi(draft_en, draft_es),
            },
        )
    maintenance = bi(
        ["Maintenance starts 02:00 UTC", "Expected duration 30 minutes", "States impact"],
        ["El mantenimiento comienza a las 02:00 UTC", "Duración prevista de 30 minutos", "Indica el impacto"],
    )
    return [
        s("clear", "publish_candidate", "Try the Free Preview with no card required. Reflex returns a recommendation; your application keeps authority over actions.", "Prueba la Vista previa gratuita sin tarjeta. Reflex devuelve una recomendación; tu aplicación conserva la autoridad sobre las acciones."),
        s("clear", "publish_candidate", "The Free Preview requires no card and provides recommendations only; execution stays in your application.", "La Vista previa gratuita no requiere tarjeta y solo ofrece recomendaciones; la ejecución permanece en tu aplicación."),
        s("clear", "reject", "Connect a card and let Reflex automatically execute every action for you.", "Conecta una tarjeta y deja que Reflex ejecute automáticamente todas las acciones."),
        s("clear", "reject", "Our new image generator creates beautiful campaign art.", "Nuestro nuevo generador de imágenes crea arte atractivo para campañas."),
        s("clear", "reject", "The preview is paid, requires a card, and automatically applies every recommendation.", "La vista previa es de pago, requiere tarjeta y aplica automáticamente cada recomendación."),
        s("boundary", "revise", "Try the Free Preview. Reflex gives a recommendation for your workflow.", "Prueba la Vista previa gratuita. Reflex ofrece una recomendación para tu flujo de trabajo."),
        s("boundary", "revise", "Maintenance starts at 02:00 UTC and should last 30 minutes.", "El mantenimiento comienza a las 02:00 UTC y debería durar 30 minutos.", maintenance),
        s("boundary", "revise", "Free Preview, no card required. Reflex will take care of the actions after recommending them.", "Vista previa gratuita, sin tarjeta. Reflex se encargará de las acciones después de recomendarlas."),
        s("boundary", "revise", "No card is needed. Reflex recommends next steps.", "No se necesita tarjeta. Reflex recomienda los siguientes pasos."),
        s("boundary", "revise", "The Free Preview needs no card and returns recommendations, although one sentence later says actions happen automatically.", "La Vista previa gratuita no necesita tarjeta y devuelve recomendaciones, aunque una frase posterior dice que las acciones ocurren automáticamente."),
        s("ambiguous", "revise", "The preview is probably free and normally does not ask for a card.", "La vista previa probablemente sea gratuita y normalmente no pide tarjeta."),
        s("ambiguous", "revise", "Maintenance starts at 02:00 UTC; another paragraph says 03:00 UTC. Expected duration is 30 minutes.", "El mantenimiento empieza a las 02:00 UTC; otro párrafo dice 03:00 UTC. La duración prevista es de 30 minutos.", maintenance),
        s("ambiguous", "revise", "After a long introduction, the final paragraph says the preview is free and recommendations are optional; card requirements are not stated.", "Tras una introducción larga, el último párrafo dice que la vista previa es gratuita y las recomendaciones son opcionales; no se aclara si se necesita tarjeta."),
        s("ambiguous", "revise", "The Free Preview usually needs no card and gives a recommendation only.", "La Vista previa gratuita normalmente no necesita tarjeta y solo da una recomendación."),
        s("ambiguous", "revise", "Reflex returns a recommendation, then your workflow may continue automatically depending on configuration; no card information is given.", "Reflex devuelve una recomendación y luego el flujo podría continuar automáticamente según la configuración; no se informa sobre la tarjeta."),
    ]


def consistency() -> list[tuple[str, str, dict[str, Any]]]:
    def s(cls, expected, fields, en, es):
        return (
            cls,
            expected,
            {
                "deterministicValidationsPassed": True,
                "normalizedRecord": fields,
                "semanticSummary": bi(en, es),
            },
        )
    return [
        s("clear", "continue_candidate", {"status": "approved", "access": "enabled"}, "The record is approved and access is enabled.", "El registro está aprobado y el acceso está habilitado."),
        s("clear", "continue_candidate", {"status": "cancelled", "renewal": "stopped"}, "The subscription is cancelled and will not renew.", "La suscripción está cancelada y no se renovará."),
        s("clear", "continue_candidate", {"shipmentStatus": "delayed", "deliveryWindow": "later"}, "The shipment is delayed and the delivery window moved later.", "El envío está retrasado y la ventana de entrega se desplazó."),
        s("clear", "exception_review", {"role": "viewer", "writePermission": False}, "The user can edit and publish records.", "El usuario puede editar y publicar registros."),
        s("clear", "exception_review", {"accountStatus": "inactive", "loginAllowed": False}, "The account is active and the user can sign in normally.", "La cuenta está activa y el usuario puede iniciar sesión con normalidad."),
        s("boundary", "review", {"status": "pending", "approvalDecision": None}, "The request looks likely to be approved soon.", "La solicitud parece probable que sea aprobada pronto."),
        s("boundary", "review", {"priority": "medium", "slaHours": 24}, "This may be a high-priority case, but impact details are incomplete.", "Podría ser un caso de alta prioridad, pero faltan detalles del impacto."),
        s("boundary", "review", {"locale": "en-GB", "region": "GB"}, "The record appears intended for UK customers, though the business scope is not stated.", "El registro parece destinado a clientes del Reino Unido, aunque no se indica el alcance comercial."),
        s("boundary", "review", {"accountStatus": "active", "integrationStatus": "disabled"}, "The account is active, but one important integration is disabled.", "La cuenta está activa, pero una integración importante está deshabilitada."),
        s("boundary", "review", {"plan": "trial", "billingStatus": "no_invoice"}, "The customer is evaluating a paid plan.", "El cliente está evaluando un plan de pago."),
        s("ambiguous", "review", {"currentStatus": "pending", "previousStatus": "approved"}, "The item is described as both pending and approved without a timestamp.", "El elemento se describe como pendiente y aprobado sin marca temporal."),
        s("ambiguous", "review", {"status": "active", "featureFlag": None}, "The main record is active; feature availability is not described.", "El registro principal está activo; no se describe la disponibilidad de la función."),
        s("ambiguous", "review", {"role": "editor", "restrictedFields": ["billing"]}, "The user has editing access, with some unspecified limitations.", "El usuario tiene acceso de edición, con algunas limitaciones no especificadas."),
        s("ambiguous", "review", {"sourceA": "enabled", "sourceB": "disabled", "authoritySource": None}, "One source says enabled and another says disabled; no authoritative source is identified.", "Una fuente dice habilitado y otra deshabilitado; no se identifica una fuente autoritativa."),
        s("ambiguous", "review", {"state": "active", "transition": "requested"}, "The entity is active while a state transition is requested; the transition outcome is not known.", "La entidad está activa mientras se solicita una transición de estado; no se conoce el resultado."),
    ]


def build() -> list[dict[str, Any]]:
    matrices = {
        "sales-lead-fit": sales(),
        "customer-support-ticket-triage": support(),
        "software-issue-triage": issues(),
        "content-quality-gate": content_quality(),
        "semantic-data-consistency": consistency(),
    }
    rows = []
    for workflow, scenarios in matrices.items():
        if len(scenarios) != 15:
            raise ValueError(f"{workflow}: expected 15 scenario pairs, got {len(scenarios)}")
        for index, (case_class, expected, state) in enumerate(scenarios, 1):
            for language in ("en", "es"):
                rows.append(make_case(workflow, index, case_class, expected, state, language))
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--procedure", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    ap.add_argument("--manifest", required=True, type=Path)
    args = ap.parse_args()
    procedure = json.loads(args.procedure.read_text())
    if procedure["status"] != "frozen-before-case-pack-and-engine-inference":
        raise SystemExit("procedure is not frozen")
    rows = build()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        "".join(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n" for r in rows)
    )
    manifest = {
        "schema": "brida.reflexbench.core-v1-workflow-case-pack/v1alpha1",
        "status": "frozen-before-engine-inference",
        "procedure_file": args.procedure.name,
        "procedure_sha256": sha256(args.procedure),
        "case_pack_file": args.output.name,
        "case_pack_sha256": sha256(args.output),
        "rows": len(rows),
        "paired_scenarios": len(rows) // 2,
        "languages": ["en", "es"],
        "evidenceClass": EVIDENCE_CLASS,
        "model_outputs_observed_before_freeze": False,
    }
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
