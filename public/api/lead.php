<?php
/**
 * Заготовка обработчика формы заявки: пересылает заявку в Telegram.
 * [куда отправлять заявки — уточнить]
 *
 * Как включить:
 * 1. Создайте бота у @BotFather, получите токен.
 * 2. Узнайте chat_id чата, куда слать заявки.
 * 3. Впишите их ниже (или задайте переменными окружения на хостинге).
 * 4. В src/data/site.ts поставьте leadForm.endpoint = '/api/lead.php' и пересоберите сайт.
 */
$TOKEN   = getenv('RL_TG_TOKEN') ?: '';   // [токен бота — уточнить]
$CHAT_ID = getenv('RL_TG_CHAT')  ?: '';   // [chat_id — уточнить]

header('Content-Type: application/json; charset=utf-8');
if ($_SERVER['REQUEST_METHOD'] !== 'POST') { http_response_code(405); exit('{"ok":false}'); }

$d = json_decode(file_get_contents('php://input'), true) ?: [];
$f = fn($k, $n = 500) => mb_substr(trim(strip_tags((string)($d[$k] ?? ''))), 0, $n);

if (!$f('name') || !$f('contact') || ($d['consent'] ?? '') !== 'on') {
  http_response_code(422); exit('{"ok":false,"error":"validation"}');
}
if (!$TOKEN || !$CHAT_ID) { http_response_code(503); exit('{"ok":false,"error":"not_configured"}'); }

$text = "Заявка с сайта\n"
  . "Имя: {$f('name')}\nКонтакт: {$f('contact')}\nСайт: {$f('site')}\n"
  . "Что беспокоит: {$f('message', 2000)}\nИсточник: {$f('source')} {$f('page')}\n"
  . "Согласие на обработку ПДн: да, " . date('c');

$ctx = stream_context_create(['http' => [
  'method' => 'POST',
  'header' => "Content-Type: application/json\r\n",
  'content' => json_encode(['chat_id' => $CHAT_ID, 'text' => $text]),
  'timeout' => 10,
]]);
$r = @file_get_contents("https://api.telegram.org/bot{$TOKEN}/sendMessage", false, $ctx);
echo $r ? '{"ok":true}' : '{"ok":false}';
if (!$r) http_response_code(502);
