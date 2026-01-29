import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';
import exec from 'k6/execution';

// Custom metrics
const errorRate = new Rate('errors');
const responseTime = new Trend('response_time');

export const options = {
  scenarios: {
    "ramping_rps": {
        "executor": "ramping-arrival-rate",
        "startRate": 0,
        "timeUnit": "1s",
        "preAllocatedVUs": 1000,
        "maxVUs": 1000,
        "stages": [
            {
                "duration": "10s",
                "target": 100
            },
            {
                "duration": "10s",
                "target": 200
            },
            {
                "duration": "10s",
                "target": 400
            }
        ]
    }
},
  thresholds: {
    "http_req_duration": [
        "p(95)<500"
    ],
    "http_req_failed": [
        "rate<0.01"
    ]
}
};

export default function () {
  const url = 'https://uat-wxmall.mova-tech.com/main/goods/list';
  
  const params = {
    headers: {
      "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.68(0x1800442b) NetType/WIFI Language/zh_CN",
      "Accept-Encoding": "gzip,compress,br,deflate",
      "Content-Type": "application/x-www-form-urlencoded",
      "wx-version": "v1.0.0",
      "app-version": "",
      "accessToken": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiIsImp0aSI6IjYzODU0NkdGRGRmczYifQ.eyJhdWQiOiJodHRwczpcL1wvd3htYWxsLm1vdmEtdGVjaC5jb20iLCJpc3MiOiJodHRwOlwvXC91YXQtd3htYWxsLm1vdmEtdGVjaC5jb20iLCJqdGkiOiI2Mzg1NDZHRkRkZnM2IiwiaWF0IjoxNzY5NTk0NjMwLCJuYmYiOjE3Njk1OTQ2MzAsImV4cCI6MTc2OTY4MTAzMCwidWlkIjoiNTU1NmNhYjgtZDc3Ni0zYWI1LThkNGMtN2Y0MDRlZjJkYWM2IiwianNvbl9kYXRhIjoie1wiaWRcIjpcIjIzMFwiLFwidXNlcl9pZFwiOlwiNTU1NmNhYjgtZDc3Ni0zYWI1LThkNGMtN2Y0MDRlZjJkYWM2XCIsXCJuaWNrXCI6XCJcIixcInJlYWxfbmFtZVwiOlwiXCIsXCJiaXJ0aGRheVwiOlwiMFwiLFwiYXJlYVwiOlwiXCIsXCJzdGF0dXNcIjpcIjBcIixcImFnZVwiOlwiMjJcIixcImF2YXRhclwiOlwiXCIsXCJhY3RpdmVfdGltZVwiOlwiMTc2OTU5NDYzMFwiLFwic2V4XCI6XCIwXCIsXCJpc19uZXdfZ2lmdFwiOlwiMFwiLFwicmVnX3Jld2FyZF9wb2ludFwiOlwiMFwiLFwicmVnX3Jld2FyZF9jb3VudFwiOlwiMFwiLFwicmVnX3BvcHVwX2NvdW50XCI6XCIwXCIsXCJjb3Vwb25fcmV3YXJkX2NvdW50XCI6XCIwXCIsXCJjb3Vwb25fcG9wdXBfY291bnRcIjpcIjBcIixcInBvaW50X3Jld2FyZF9jb3VudFwiOlwiMFwiLFwicG9pbnRfcG9wdXBfY291bnRcIjpcIjBcIixcIm9waWRcIjpcIjU0YWQ5YTI4ZmQ3NzA2NzdcIn0iLCJ2ZXJzaW9uIjoiMS4wLjEifQ.HwBdCSBgPfLl8xds5UT6RpyvwLndf1n55laCoGgJfsE",
      "os": "",
      "Referer": "https://servicewechat.com/wx62b84aabaf520f99/0/page-frame.html"
},
  };
  
  const payload = `tid=-1&page=3&page_size=10&user_id=5556cab8-d776-3ab5-8d4c-7f404ef2dac6&api=i_1643178026&version=2.1.3&union=&euid=0&cps=&referer=pages%2Findex%2Findex&sign_time=1769594640&sign=f8506c2a5453a1749e38a493992e146b`;
  
  const res = http.post(url, payload, params);
  
  // Record metrics
  responseTime.add(res.timings.duration);
  
  // Check response
  const checkResult = check(res, {
    'status is 2xx': (r) => r.status >= 200 && r.status < 300,
    'response time < 2000ms': (r) => r.timings.duration < 2000,
  });
  
  errorRate.add(!checkResult);
  
  // Log error details if failed
  if (res.status >= 400 || res.status === 0) {
    console.error(`[Request Error] Status: ${res.status}, URL: ${url}`);
    console.error(`[Request Error] Response Body: ${res.body}`);
    exec.test.abort('Aborting test due to failure (Status ${res.status})');
  }
  
  sleep(1);
}

export function handleSummary(data) {
  return {
    'stdout': JSON.stringify(data, null, 2),
  };
}
