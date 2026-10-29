# Copyright (c) 2026 Paulo Henrik Carvalho Araújo
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import asyncio
import json
import time
import websockets
import sys

status_file = r'C:\CineGen\scripts\live_status.json'

def update_status(data):
    try:
        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass

async def monitor():
    uri = 'ws://127.0.0.1:8188/ws?clientId=mon_continuous'
    print('Connecting to ComfyUI WebSocket...', flush=True)
    async with websockets.connect(uri) as ws:
        print('Connected! Monitoring generation progress until complete...', flush=True)
        current_state = {'status': 'monitoring', 'step': 0, 'max_steps': 10, 'current_node': None, 'last_update': time.strftime('%H:%M:%S')}
        update_status(current_state)
        while True:
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=2.0)
                if isinstance(msg, str):
                    d = json.loads(msg)
                    mtype = d.get('type')
                    data = d.get('data', {})
                    ts = time.strftime('%H:%M:%S')
                    current_state['last_update'] = ts
                    if mtype == 'progress':
                        val = data.get('value')
                        mx = data.get('max')
                        node = data.get('node')
                        current_state.update({'step': val, 'max_steps': mx, 'current_node': node, 'status': 'sampling'})
                        update_status(current_state)
                        print(f"[{ts}] Progress: Step {val}/{mx} (Node {node})", flush=True)
                    elif mtype == 'executing':
                        node = data.get('node')
                        current_state['current_node'] = node
                        if node is None:
                            current_state['status'] = 'completed'
                            update_status(current_state)
                            print(f"[{ts}] Execution completed!", flush=True)
                            break
                        else:
                            current_state['status'] = f'executing_node_{node}'
                            update_status(current_state)
                            print(f"[{ts}] Executing Node {node}...", flush=True)
                    elif mtype == 'executed':
                        node = data.get('node')
                        print(f"[{ts}] Node {node} executed successfully.", flush=True)
                    elif mtype == 'execution_error':
                        current_state['status'] = 'error'
                        current_state['error'] = data
                        update_status(current_state)
                        print(f"[{ts}] ERROR: {data}", flush=True)
                        break
            except asyncio.TimeoutError:
                pass

if __name__ == '__main__':
    asyncio.run(monitor())
