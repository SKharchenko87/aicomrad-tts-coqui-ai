import asyncio
import aiohttp
import time
import argparse
import statistics
from datetime import datetime

async def synthesize_request(session, url, text, request_id):
    start_time = time.time()
    try:
        async with session.post(url, data={
            'text': text,
            'language': 'ru',
            'speaker': 'female-1',
            'fmt': 'wav',
            'model_id': 'xtts-v2'
        }) as response:
            content = await response.read()
            duration = time.time() - start_time
            status = response.status
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Request {request_id}: Status {status}, Time {duration:.2f}s")
            return duration, status
    except Exception as e:
        print(f"Request {request_id} failed: {e}")
        return 0, 0

async def run_test(num_requests, url):
    print(f"\nStarting test with {num_requests} parallel requests...")
    print(f"Target URL: {url}")
    
    text = "Привет! Это тест производительности синтеза речи при параллельной нагрузке."
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        start_total = time.time()
        
        for i in range(num_requests):
            task = asyncio.create_task(synthesize_request(session, url, text, i+1))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_total
        
    durations = [r[0] for r in results if r[1] == 200]
    success_count = len(durations)
    
    print(f"\n{'='*40}")
    print(f"Test Results ({num_requests} requests)")
    print(f"{'='*40}")
    print(f"Successful requests: {success_count}/{num_requests}")
    print(f"Total time: {total_time:.2f}s")
    
    if durations:
        print(f"Average time per request: {statistics.mean(durations):.2f}s")
        print(f"Median time: {statistics.median(durations):.2f}s")
        print(f"Min time: {min(durations):.2f}s")
        print(f"Max time: {max(durations):.2f}s")
        print(f"Throughput: {success_count / total_time:.2f} req/s")
    print(f"{'='*40}\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='TTS Performance Test')
    parser.add_argument('--url', default='http://localhost:5000/synthesize', help='TTS API URL')
    parser.add_argument('--requests', type=int, default=5, help='Number of parallel requests')
    args = parser.parse_args()
    
    asyncio.run(run_test(args.requests, args.url))
