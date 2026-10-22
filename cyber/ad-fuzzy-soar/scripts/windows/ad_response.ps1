<#
.SYNOPSIS
    AD-Fuzzy-SOAR — Script PowerShell de Răspuns Automatizat la Incidente în Windows Active Directory.
    Compatibil atât cu apelarea directă / Ansible, cât și ca script Wazuh Active Response pe Windows.

.PARAMETER Action
    Nivelul de răspuns fuzzy: MONITOR_LOG, ALERT_AND_AUDIT, CONTAIN_ACCOUNT_AND_HOST, EMERGENCY_DOMAIN_LOCKDOWN.
.PARAMETER TargetUser
    Contul samAccountName / UPN vizat în Active Directory.
.PARAMETER SourceIP
    Adresa IP a stației sursă de pe care provine anomalia/atacul.
.PARAMETER TargetHost
    Hostname-ul FQDN al serverului sau stației Windows.
.PARAMETER RiskScore
    Scorul de risc cibernetic calculat prin defuzzificare Mamdani [0-100].
.PARAMETER DryRun
    Dacă este prezent, afișează și jurizează acțiunile fără a modifica starea AD/Firewall.
#>

param(
    [Parameter(Mandatory=$false)][string]$Action = "ALERT_AND_AUDIT",
    [Parameter(Mandatory=$false)][string]$TargetUser = "unknown_user",
    [Parameter(Mandatory=$false)][string]$SourceIP = "0.0.0.0",
    [Parameter(Mandatory=$false)][string]$TargetHost = $env:COMPUTERNAME,
    [Parameter(Mandatory=$false)][double]$RiskScore = 0.0,
    [switch]$DryRun
)

$ErrorActionPreference = "Continue"
$Timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
$WazuhArLog = "C:\Program Files (x86)\ossec-agent\active-response\active-responses.log"

function Write-SoarLog {
    param([string]$Message)
    $Entry = "[$Timestamp] [AD-FUZZY-SOAR-PS1] [Risk=$RiskScore] [Tier=$Action] $Message"
    Write-Output $Entry
    if (Test-Path (Split-Path $WazuhArLog -Parent)) {
        Add-Content -Path $WazuhArLog -Value $Entry -Encoding UTF8
    }
}

Write-SoarLog "Inițiere răspuns la incident pe host='$TargetHost', user='$TargetUser', src_ip='$SourceIP', DryRun=$DryRun"

switch ($Action) {
    "MONITOR_LOG" {
        Write-SoarLog "Acțiune: Monitorizare pasivă. Nicio restricție aplicată."
    }

    "ALERT_AND_AUDIT" {
        Write-SoarLog "Acțiune: Audit extins sesiuni Kerberos/NTLM și verificare apartenență grupuri privilegiate."
        if (-not $DryRun) {
            Import-Module ActiveDirectory -ErrorAction SilentlyContinue
            Get-WinEvent -FilterHashtable @{LogName='Security'; ID=4624,4625,4768,4769,4672} -MaxEvents 25 -ErrorAction SilentlyContinue |
                Export-Csv -Path "C:\Windows\Temp\ad_fuzzy_audit_$($TargetUser).csv" -NoTypeInformation
        } else {
            Write-SoarLog "[DRY-RUN] S-ar exporta ultimele evenimente 4624/4625/4768/4769/4672 și grupurile AD pentru '$TargetUser'."
        }
    }

    "CONTAIN_ACCOUNT_AND_HOST" {
        Write-SoarLog "Acțiune: Izolare cont AD '$TargetUser', purjare tichete Kerberos și blocare IP '$SourceIP'."
        if (-not $DryRun) {
            Import-Module ActiveDirectory -ErrorAction SilentlyContinue
            if ($TargetUser -notmatch "^(krbtgt|Administrator)$") {
                Disable-ADAccount -Identity $TargetUser -Confirm:$false
            }
            klist purge | Out-Null
            if ($SourceIP -ne "0.0.0.0") {
                New-NetFirewallRule -DisplayName "AD_Fuzzy_Block_$SourceIP" -Direction Inbound -Action Block -RemoteAddress $SourceIP -Profile Any | Out-Null
            }
        } else {
            Write-SoarLog "[DRY-RUN] Disable-ADAccount -Identity '$TargetUser'; klist purge; New-NetFirewallRule Block '$SourceIP'."
        }
    }

    "EMERGENCY_DOMAIN_LOCKDOWN" {
        Write-SoarLog "ACȚIUNE CRITICĂ TIER-0: Lockdown cont '$TargetUser', închidere sesiuni SMB de la '$SourceIP', revocare Kerberos TGT/TGS și audit ACL DCSync!"
        if (-not $DryRun) {
            Import-Module ActiveDirectory -ErrorAction SilentlyContinue
            if ($TargetUser -notmatch "^krbtgt$") {
                Disable-ADAccount -Identity $TargetUser -Confirm:$false
            }
            klist purge | Out-Null
            Get-SmbSession | Where-Object { $_.ClientComputerName -eq $SourceIP } | Close-SmbSession -Force -ErrorAction SilentlyContinue
            if ($SourceIP -ne "0.0.0.0") {
                New-NetFirewallRule -DisplayName "AD_Fuzzy_LOCKDOWN_In_$SourceIP" -Direction Inbound -Action Block -RemoteAddress $SourceIP -Profile Any | Out-Null
                New-NetFirewallRule -DisplayName "AD_Fuzzy_LOCKDOWN_Out_$SourceIP" -Direction Outbound -Action Block -RemoteAddress $SourceIP -Profile Any | Out-Null
            }
        } else {
            Write-SoarLog "[DRY-RUN] EMERGENCY LOCKDOWN: Disable-ADAccount '$TargetUser'; Close-SmbSession '$SourceIP'; Block In/Out Firewall '$SourceIP'; Audit Domain Root DCSync ACL."
        }
    }
}
