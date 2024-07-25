import asyncio
import websockets


async def test_websocket():
    uri = "ws://localhost:8009/ws/some_value"
    async with websockets.connect(uri) as websocket:
        # 等待连接建立
        await asyncio.sleep(1)  # 这里等待1秒，确保连接已建立

        # 发送消息
        await websocket.send("Hello WebSocket!")

        # 接收消息
        response = await websocket.recv()
        print("Received:", response)


# 运行测试函数
asyncio.run(test_websocket())
