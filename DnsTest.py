#!/usr/bin/env python3
import subprocess
import time
import requests

# Список DNS-серверов с DoH и DoT адресами
servers = [
    {"name": "Google Public DNS", "doh_url": "https://dns.google/dns-query", "dot_host": "dns.google", "dot_port": 853},
    {"name": "Cloudflare DNS", "doh_url": "https://cloudflare-dns.com/dns-query", "dot_host": "1.1.1.1", "dot_port": 853},
    {"name": "Yandex DNS", "doh_url": "https://dns.yandex.ru/dns-query", "dot_host": "common.dot.dns.yandex.net", "dot_port": 853},
    {"name": "Quad9", "doh_url": "https://dns.quad9.net/dns-query", "dot_host": "dns.quad9.net", "dot_port": 853},
    {"name": "AdGuard DNS", "doh_url": "https://dns.adguard.com/dns-query", "dot_host": "dns.adguard-dns.com", "dot_port": 853},
    {"name": "OpenDNS", "doh_url": "https://doh.opendns.com/dns-query", "dot_host": "dns.opendns.com", "dot_port": 853},
    {"name": "Comodo Secure DNS", "doh_url": "https://dns.comss.one/dns-query", "dot_host": "dns.comss.one", "dot_port": 853},
    {"name": "CleanBrowsing Family Filter", "doh_url": "https://doh.cleanbrowsing.org/doh/family-filter/", "dot_host": "family-filter-dns.cleanbrowsing.org", "dot_port": 853},
    {"name": "AliDNS", "doh_url": "https://dns.alidns.com/dns-query", "dot_host": "dns.alidns.com", "dot_port": 853},
    {"name": "BebasDNS", "doh_url": "https://dns.bebasid.com/dns-query", "dot_host": "dns.bebasid.com", "dot_port": 853},
    {"name": "CaliphDNS", "doh_url": "https://dns.caliph.dev/dns-query", "dot_host": "dns.caliph.dev", "dot_port": 853}
]

# Расширенный список популярных доменов для теста
test_domains = [
    "example.com", "google.com", "yandex.ru", "cloudflare.com", "wikipedia.org",
    "youtube.com", "facebook.com", "vk.com", "mail.ru", "rambler.ru",
    "twitch.tv", "twitter.com", "instagram.com", "stackoverflow.com", "github.com",
    "reddit.com", "amazon.com", "netflix.com", "bbc.co.uk", "cnn.com",
    "live.com", "microsoft.com", "apple.com", "mozilla.org", "linkedin.com",
    "ok.ru", "aliexpress.com", "ebay.com", "dropbox.com", "paypal.com",
    "adobe.com", "spotify.com", "zoom.us", "slack.com", "wordpress.org",
    "medium.com", "quora.com", "duckduckgo.com", "bitbucket.org", "digitalocean.com",
    "heroku.com", "oracle.com", "salesforce.com", "shopify.com", "tumblr.com",
    "bbc.com", "nytimes.com", "forbes.com", "theguardian.com", "etsy.com",
    "tripadvisor.com", "booking.com", "airbnb.com", "craigslist.org", "walmart.com",
    "target.com", "bestbuy.com", "ikea.com", "huffpost.com", "buzzfeed.com",
    "yahoo.com", "bing.com", "yelp.com"
]

output_file = "dns_speed_results.txt"

def build_dns_query(domain):
    parts = domain.split('.')
    query = b'\x00\x00'  # ID
    query += b'\x01\x00'  # стандартный запрос
    query += b'\x00\x01'  # один вопрос
    query += b'\x00\x00'  # нет ответов
    query += b'\x00\x00'  # нет авторитетных ответов
    query += b'\x00\x00'  # нет дополнительных записей
    for part in parts:
        query += bytes([len(part)]) + part.encode()
    query += b'\x00'  # конец имени
    query += b'\x00\x01'  # тип A
    query += b'\x00\x01'  # класс IN
    return query

def test_doh(url, domain):
    headers = {'accept': 'application/dns-message'}
    data = build_dns_query(domain)
    try:
        start = time.time()
        response = requests.post(url, data=data, headers=headers, timeout=5)
        response.raise_for_status()
        elapsed = time.time() - start
        return elapsed
    except Exception:
        return None

def test_dot(host, port, domain):
    cmd = [
        "kdig",
        f"@{host}",
        "-p", str(port),
        "+tls-ca",
        f"+tls-host={host}",
        domain
    ]
    try:
        start = time.time()
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5, check=True)
        elapsed = time.time() - start
        return elapsed
    except Exception:
        return None

def main():
    results = []
    print(f"Тестируем скорость DoH и DoT серверов для доменов: {', '.join(test_domains)}\n")

    for s in servers:
        doh_times = []
        dot_times = []
        print(f"Провайдер: {s['name']}")

        for domain in test_domains:
            doh_time = test_doh(s['doh_url'], domain)
            dot_time = test_dot(s['dot_host'], s['dot_port'], domain)
            if doh_time is not None:
                doh_times.append(doh_time)
            if dot_time is not None:
                dot_times.append(dot_time)

        avg_doh = sum(doh_times)/len(doh_times) if doh_times else None
        avg_dot = sum(dot_times)/len(dot_times) if dot_times else None

        results.append((s['name'], s['doh_url'], avg_doh, s['dot_host'], avg_dot))

        print(f"  Среднее время DoH: {avg_doh:.3f} с" if avg_doh is not None else "  DoH: ошибка")
        print(f"  Среднее время DoT: {avg_dot:.3f} с" if avg_dot is not None else "  DoT: ошибка")
        print()

    doh_sorted = sorted([r for r in results if r[2] is not None], key=lambda x: x[2])
    dot_sorted = sorted([r for r in results if r[4] is not None], key=lambda x: x[4])

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("=== Отчёт по DNS серверам (среднее время по списку доменов) ===\n\n")

        f.write("DoH (DNS-over-HTTPS) - отсортировано по скорости:\n")
        for name, doh_url, doh_time, _, _ in doh_sorted:
            f.write(f"DoH {doh_url} {doh_time:.3f}s {name}\n")
        f.write("\n")

        f.write("DoT (DNS-over-TLS) - отсортировано по скорости:\n")
        for name, _, _, dot_host, dot_time in dot_sorted:
            f.write(f"DoT {dot_host}:853 {dot_time:.3f}s {name}\n")
        f.write("\n")

        f.write("=== Отдельный список адресов DoH, отсортированных по скорости ===\n")
        for _, doh_url, _, _, _ in doh_sorted:
            f.write(doh_url + "\n")
        f.write("\n")

        f.write("=== Отдельный список адресов DoT, отсортированных по скорости ===\n")
        for _, _, _, dot_host, _ in dot_sorted:
            f.write(dot_host + "\n")

    print(f"Результаты сохранены в файл '{output_file}'")

if __name__ == "__main__":
    main()
