import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const responseTime = new Trend('response_time');

export const options = {
  scenarios: {
    "ramping_rps": {
        "executor": "ramping-arrival-rate",
        "startRate": 0,
        "timeUnit": "1s",
        "preAllocatedVUs": 10,
        "maxVUs": 100,
        "stages": [
            {
                "duration": "10s",
                "target": 100
            },
            {
                "duration": "20s",
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
  const url = 'https://uat-wxmall.mova-tech.com/main/login/index';
  
  const params = {
    headers: {
      "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.68(0x1800442a) NetType/WIFI Language/zh_CN",
      "Accept-Encoding": "gzip,compress,br,deflate",
      "Content-Type": "application/x-www-form-urlencoded",
      "wx-version": "v1.0.0",
      "app-version": "0.0.0",
      "accessToken": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiIsImp0aSI6IjYzODU0NkdGRGRmczYifQ.eyJhdWQiOiJodHRwczpcL1wvd3htYWxsLm1vdmEtdGVjaC5jb20iLCJpc3MiOiJodHRwOlwvXC91YXQtd3htYWxsLm1vdmEtdGVjaC5jb20iLCJqdGkiOiI2Mzg1NDZHRkRkZnM2IiwiaWF0IjoxNzY5NDEzNTY5LCJuYmYiOjE3Njk0MTM1NjksImV4cCI6MTc2OTQ5OTk2OSwidWlkIjoiNTU1NmNhYjgtZDc3Ni0zYWI1LThkNGMtN2Y0MDRlZjJkYWM2IiwianNvbl9kYXRhIjoie1wib3BlbnVkaWRcIjpcIm9ocUJ3N1ZITWNnc0x2clJhQTNRQk5hTzlsMDRcIixcInVuaW9uaWRcIjpcIm9PWm1BNklZWnFfLWNBWWpFU1VmVXlVMjBOSFVcIixcIm5pY2tcIjpcIlwiLFwiYXZhdGFyXCI6XCJcIixcImFnZVwiOjIyLFwic2V4XCI6MCxcInVzZXJfaWRcIjpcIjU1NTZjYWI4LWQ3NzYtM2FiNS04ZDRjLTdmNDA0ZWYyZGFjNlwiLFwiaXNSZWdpc3RlckZsYWdcIjoxLFwiaXNSZWdpc3RlclwiOjEsXCJpc1RvZGF5Rmlyc3RcIjoxLFwidXNlcl90eXBlXCI6XCIxXCIsXCJvcGlkXCI6XCI1NGFkOWEyOGZkNzcwNjc3XCJ9IiwidmVyc2lvbiI6IjEuMC4xIn0.r_maUiiNvg3IrMdgR07C2kwJasHs_2yfuGgI_vAoSIk",
      "os": "iOS-%E5%B0%8F%E7%A8%8B%E5%BA%8F",
      "Referer": "https://servicewechat.com/wx62b84aabaf520f99/0/page-frame.html"
},
  };
  
  const payload = `openudid=0e31U80w359Np63r9Y1w3W7wcm11U80&user_type=1&login_type=1&isFrame=1&source=1089&r_code&log_code&invite_user_id&user_id=0&api=i_1643178026&version=2.1.3&union&euid=0&cps&referer=pages/index/index&sign_time=1769413572&sign=74d43cbb036876073239a23eb71361d6&provider=test`;
  
  const res = http.post(url, payload, params);
  
  // Record metrics
  responseTime.add(res.timings.duration);
  
  // Check response
  const checkResult = check(res, {
    'status is 2xx': (r) => r.status >= 200 && r.status < 300,
    'response time < 2000ms': (r) => r.timings.duration < 2000,
  });
  
  errorRate.add(!checkResult);
  
  sleep(1);
}

export function handleSummary(data) {
  return {
    'stdout': JSON.stringify(data, null, 2),
  };
}
