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
  const url = 'https://uat-wxmall.mova-tech.com/main/order/buy-info';
  
  const params = {
    headers: {
      "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.68(0x1800442a) NetType/WIFI Language/zh_CN",
      "Accept-Encoding": "gzip,compress,br,deflate",
      "Content-Type": "application/x-www-form-urlencoded",
      "wx-version": "v1.0.0",
      "app-version": "0.0.0",
      "accessToken": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiIsImp0aSI6IjYzODU0NkdGRGRmczYifQ.eyJhdWQiOiJodHRwczpcL1wvd3htYWxsLm1vdmEtdGVjaC5jb20iLCJpc3MiOiJodHRwOlwvXC91YXQtd3htYWxsLm1vdmEtdGVjaC5jb20iLCJqdGkiOiI2Mzg1NDZHRkRkZnM2IiwiaWF0IjoxNzY5NDgzMzAwLCJuYmYiOjE3Njk0ODMzMDAsImV4cCI6MTc2OTU2OTcwMCwidWlkIjoiNDcxMjYiLCJqc29uX2RhdGEiOiJ7XCJpZFwiOlwiMTY1N1wiLFwidXNlcl9pZFwiOlwiNDcxMjZcIixcIm5pY2tcIjpcIlBONDcwNjYyXCIsXCJyZWFsX25hbWVcIjpcIlwiLFwiYmlydGhkYXlcIjpcIjBcIixcImFyZWFcIjpcIlwiLFwic3RhdHVzXCI6XCIwXCIsXCJhZ2VcIjpcIjIyXCIsXCJhdmF0YXJcIjpcIlwiLFwiYWN0aXZlX3RpbWVcIjpcIjE3Njk0ODMzMDBcIixcInNleFwiOlwiMFwiLFwiaXNfbmV3X2dpZnRcIjpcIjFcIixcInJlZ19yZXdhcmRfcG9pbnRcIjpcIjBcIixcInJlZ19yZXdhcmRfY291bnRcIjpcIjBcIixcInJlZ19wb3B1cF9jb3VudFwiOlwiMFwiLFwiY291cG9uX3Jld2FyZF9jb3VudFwiOlwiMFwiLFwiY291cG9uX3BvcHVwX2NvdW50XCI6XCIwXCIsXCJwb2ludF9yZXdhcmRfY291bnRcIjpcIjBcIixcInBvaW50X3BvcHVwX2NvdW50XCI6XCIwXCIsXCJhY3RpdmVfdmVyc2lvblwiOlwiMC4wLjBcIixcImFjdGl2ZV9vc1wiOlwiaU9TLVxcdTVjMGZcXHU3YTBiXFx1NWU4ZlwiLFwib3BpZFwiOlwiNTRhZDlhMjhmZDc3MDY3N1wifSIsInZlcnNpb24iOiIxLjAuMSJ9.CGGJsW_sjh7pW5tToDWssCFwZhhvYsdtRfjZJ6z1eTA",
      "os": "iOS-%E5%B0%8F%E7%A8%8B%E5%BA%8F",
      "Referer": "https://servicewechat.com/wx62b84aabaf520f99/0/page-frame.html"
},
  };
  
  const payload = `gcombines=%5B%7B%22gid%22%3A8018%2C%22sid%22%3A%220%22%2C%22num%22%3A1%2C%22gini_id%22%3A0%2C%22channel_sku%22%3A%22%22%7D%5D&aid=0&cart_ids=&ac_data=&ac_id=0&ac_type=0&coupon_id=0&consume_id=0&coin=0&coin_type=0&gold_bars=0&gold_bars_type=0&gift_card_ids=&is_display=3&subsidy_type=0&test_user_id=47126&api=i_1643178026&version=2.1.3&union=&euid=0&cps=&referer=pages%2Findex%2Findex&sign_time=1769484829&sign=9483ca387ca6c53cae6d42a6eb42a89e`;
  
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
