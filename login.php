<?php

$ch = curl_init();

curl_setopt($ch, CURLOPT_URL, 'http://127.0.0.1:40000/login');
curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
curl_setopt($ch, CURLOPT_POST, 1);
curl_setopt($ch, CURLOPT_POSTFIELDS, "      {\n        \"username\": \"" . $argv[1] . "\",\n        \"password\": \"" . $argv[2] . "\"\n      }");

$headers = array();
$headers[] = 'Accept: */*';
$headers[] = 'User-Agent: Thunder Client (https://www.thunderclient.com)';
$headers[] = 'Content-Type: application/json';
curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);

$result = curl_exec($ch);
if (curl_errno($ch)) {
    echo 'Error:' . curl_error($ch);
}
curl_close($ch);
print_r($result);
