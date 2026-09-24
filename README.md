# FreePBX AI → IC Project — Docker

Dockerowa wersja testowa projektu **FreePBX AI → IC Project**.

Repo zawiera:
- lokalny LLM przez Ollama,
- STT przez faster-whisper,
- TTS przez Piper,
- dwukierunkowe audio z Asterisk/FreePBX przez AudioSocket,
- tworzenie zadań w IC Project przez REST API,
- prosty panel WWW,
- dwa tryby sieciowe: bezpośredni oraz przez klienta WireGuard.

## Architektura

```text
                    +------------------+
SIP/PSTN -> FreePBX | AudioSocket :9019|----+
                    +------------------+    |
                                              v
                                      +---------------+
                                      | agent / FastAPI|
                                      | VAD + Whisper |
                                      +-------+-------+
                                              |
                         +--------------------+--------------------+
                         |                                         |
                         v                                         v
                   +-----------+                             +-----------+
                   |  Ollama   |                             |   Piper   |
                   | local LLM |                             | local TTS |
                   +-----------+                             +-----------+
                         |
                         v
                  IC Project REST API
```

## Wymagania

- Docker Engine 24+
- Docker Compose v2
- 4 vCPU
- minimum 8 GB RAM
- około 20 GB wolnego miejsca na obrazy i modele

GPU nie jest wymagane do testów.

## 1. Klonowanie

```bash
git clone https://github.com/Pawel-sp9pw/freepbx-ai-icproject-docker.git
cd freepbx-ai-icproject-docker
cp .env.example .env
```

W `.env` ustaw co najmniej:

```env
ADMIN_PASSWORD=zmien-to-na-dlugie-haslo
```

## 2. Tryb bez WireGuard

```bash
docker compose --profile direct up -d --build
```

Panel:

```text
http://IP_SERWERA:8080
```

Login:

```text
admin
```

Hasło: wartość `ADMIN_PASSWORD` z `.env`.

AudioSocket:

```text
IP_SERWERA:9019/tcp
```

## 3. Tryb przez WireGuard

Ten wariant jest przydatny, gdy Docker i FreePBX stoją w różnych lokalizacjach.

Utwórz:

```text
wireguard/wg_confs/wg0.conf
```

Przykład:

```ini
[Interface]
PrivateKey = <KLUCZ_KLIENTA>
Address = 10.20.30.2/32

[Peer]
PublicKey = <KLUCZ_SERWERA>
Endpoint = vpn.example.pl:51820
AllowedIPs = 192.168.10.0/24
PersistentKeepalive = 25
```

Następnie:

```bash
docker compose --profile wireguard up -d --build
```

W tym wariancie kontener `agent-wg` współdzieli namespace sieciowy z kontenerem `wireguard`.
Dzięki temu ruch do sieci wskazanej w `AllowedIPs` idzie przez tunel.

Sprawdzenie:

```bash
docker compose exec wireguard wg show
```

### Ważne dla WireGuard

Host Docker musi mieć `/dev/net/tun`.

Sprawdzenie:

```bash
ls -l /dev/net/tun
```

Jeżeli Docker działa wewnątrz LXC Proxmox, przekazanie TUN i uprawnień `NET_ADMIN` może wymagać dodatkowej konfiguracji kontenera.

## 4. Pierwszy start modeli

Ollama pobiera domyślnie `qwen3:4b`.

Sprawdzenie:

```bash
docker compose exec ollama ollama list
```

Ręczne pobranie:

```bash
docker compose exec ollama ollama pull qwen3:4b
```

Piper podczas budowy obrazu pobiera polski głos:
`pl_PL-mc_speech-medium`.

Whisper domyślnie używa modelu `small`. Model zostanie pobrany przy pierwszej transkrypcji i zapisany w wolumenie cache.

## 5. Konfiguracja FreePBX / Asterisk

Sprawdź moduł:

```bash
asterisk -rx "module show like audiosocket"
```

Przykład w `/etc/asterisk/extensions_custom.conf`:

```ini
[ai-icproject]
exten => s,1,NoOp(AI IC Project Agent)
 same => n,Answer()
 same => n,Set(AI_UUID=${UUID()})
 same => n,AudioSocket(${AI_UUID},IP_DOCKERA:9019)
 same => n,Hangup()
```

Po zmianie:

```bash
fwconsole reload
```

W FreePBX utwórz Custom Destination:

```text
ai-icproject,s,1
```

i podepnij go do DID / IVR / kolejki.

## 6. IC Project

W panelu WWW wpisz:
- instance slug,
- token API,
- ID kolumny tablicy,
- domyślny priorytet.

Agent wysyła zadanie przez:

```text
POST https://app.icproject.com/api/instance/{INSTANCE}/project/tasks
```

Token jest przechowywany zaszyfrowany w wolumenie `agent-data`.

## 7. Porty

- `8080/tcp` — panel WWW
- `9019/tcp` — Asterisk AudioSocket
- Ollama i Piper nie są domyślnie publikowane na hosta

## 8. Logi

```bash
docker compose logs -f agent
```

W trybie WireGuard:

```bash
docker compose logs -f agent-wg wireguard
```

## 9. Healthcheck

```bash
curl http://127.0.0.1:8080/api/health
```

Powinno zwrócić:

```json
{"status":"ok"}
```

## 10. Zatrzymanie

Direct:

```bash
docker compose --profile direct down
```

WireGuard:

```bash
docker compose --profile wireguard down
```

## Status

To jest wersja testowa/MVP. Przed produkcją warto dodać m.in.:
- lepszą obsługę przerwania wypowiedzi (barge-in),
- kolejkę/retry dla IC Project,
- identyfikację klienta po CallerID,
- historię połączeń i zgłoszeń w panelu,
- HTTPS lub dostęp do panelu wyłącznie przez VPN.
