#!/usr/bin/env bash
# =============================================================================
# AD-Fuzzy-SOAR — Script Bash de Răspuns la Incidente pentru Noduri Linux
# înrolate în Active Directory (SSSD / realmd / Kerberos / PAM) & Wazuh Agent.
# =============================================================================
set -euo pipefail

ACTION="ALERT_AND_AUDIT"
TARGET_USER="unknown_user"
SRC_IP="0.0.0.0"
TARGET_HOST="$(hostname)"
RISK_SCORE="0.0"
DRY_RUN=true

while [[ $# -gt 0 ]]; do
    case "$1" in
        --action) ACTION="$2"; shift 2 ;;
        --user) TARGET_USER="$2"; shift 2 ;;
        --src-ip) SRC_IP="$2"; shift 2 ;;
        --host) TARGET_HOST="$2"; shift 2 ;;
        --risk-score) RISK_SCORE="$2"; shift 2 ;;
        --dry-run) DRY_RUN=true; shift ;;
        --execute) DRY_RUN=false; shift ;;
        *) shift ;;
    esac
done

TIMESTAMP="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
WAZUH_AR_LOG="/var/ossec/logs/active-responses.log"

log_soar() {
    local msg="[$TIMESTAMP] [AD-FUZZY-SOAR-SH] [Host=$TARGET_HOST] [Risk=$RISK_SCORE] [Tier=$ACTION] $1"
    echo "$msg"
    if [[ -w "$(dirname "$WAZUH_AR_LOG")" ]]; then
        echo "$msg" >> "$WAZUH_AR_LOG"
    fi
}

log_soar "Evaluare primită pentru user='$TARGET_USER', src_ip='$SRC_IP', dry_run=$DRY_RUN"

case "$ACTION" in
    MONITOR_LOG)
        log_soar "Monitorizare pasivă. Evenimentul a fost înregistrat fără blocare activă."
        ;;

    ALERT_AND_AUDIT)
        if [[ "$DRY_RUN" == "true" ]]; then
            log_soar "[DRY-RUN] Auditare sesiuni SSH/SSSD și cache Kerberos (/tmp/krb5cc_*) pentru '$TARGET_USER'."
        else
            log_soar "Colectare artefacte SSSD/PAM și sesiuni active pentru '$TARGET_USER'."
            who || true
            ls -la /tmp/krb5cc_* 2>/dev/null || true
        fi
        ;;

    CONTAIN_ACCOUNT_AND_HOST)
        if [[ "$DRY_RUN" == "true" ]]; then
            log_soar "[DRY-RUN] usermod -L '$TARGET_USER'; sss_cache -u '$TARGET_USER'; rm -f /tmp/krb5cc_*; ufw/iptables drop '$SRC_IP'."
        else
            log_soar "Izolare activă: blocare cont '$TARGET_USER', invalidare SSSD/Kerberos și blocare IP '$SRC_IP'."
            id "$TARGET_USER" >/dev/null 2>&1 && usermod -L "$TARGET_USER" || true
            command -v sss_cache >/dev/null 2>&1 && sss_cache -u "$TARGET_USER" || true
            rm -f /tmp/krb5cc_* 2>/dev/null || true
            if [[ "$SRC_IP" != "0.0.0.0" ]]; then
                if command -v ufw >/dev/null 2>&1; then
                    ufw insert 1 deny from "$SRC_IP" to any || true
                elif command -v iptables >/dev/null 2>&1; then
                    iptables -C INPUT -s "$SRC_IP" -j DROP 2>/dev/null || iptables -I INPUT 1 -s "$SRC_IP" -j DROP
                fi
            fi
        fi
        ;;

    EMERGENCY_DOMAIN_LOCKDOWN)
        if [[ "$DRY_RUN" == "true" ]]; then
            log_soar "[DRY-RUN] EMERGENCY LOCKDOWN: pkill -KILL -u '$TARGET_USER'; sss_cache -E; kdestroy -A; iptables DROP In/Out '$SRC_IP'."
        else
            log_soar "LOCKDOWN CRITIC: Terminare procese '$TARGET_USER', invalidare completă SSSD/Kerberos și izolare rețea '$SRC_IP'!"
            pkill -KILL -u "$TARGET_USER" 2>/dev/null || true
            command -v sss_cache >/dev/null 2>&1 && sss_cache -E || true
            rm -f /tmp/krb5cc_* 2>/dev/null || true
            if [[ "$SRC_IP" != "0.0.0.0" ]]; then
                if command -v iptables >/dev/null 2>&1; then
                    iptables -I INPUT 1 -s "$SRC_IP" -j DROP || true
                    iptables -I OUTPUT 1 -d "$SRC_IP" -j DROP || true
                fi
            fi
        fi
        ;;
esac
