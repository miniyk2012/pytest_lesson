import asyncio
import time


# 定义异步可迭代对象（必须实现 __aiter__ 和 __anext__ 方法）
class AsyncDataGenerator:
    def __init__(self, count):
        self.count = count
        self.index = 0

    # 异步可迭代对象必须实现 __aiter__，返回自身
    def __aiter__(self):
        return self

    # 异步迭代的核心：__anext__ 是异步方法，返回下一个元素
    async def __anext__(self):
        if self.index >= self.count:
            raise StopAsyncIteration  # 终止异步迭代（对应同步的 StopIteration）

        # 模拟异步IO等待（比如异步请求网络、异步读文件）
        await asyncio.sleep(1)
        self.index += 1
        return self.index - 1


async def async_data_generator(count):
    index = 0
    while index < count:
        # 模拟异步IO等待
        await asyncio.sleep(1)
        yield index  # 返回当前索引
        index += 1


# 异步处理数据
async def async_process(name, count):
    print(f"任务{name}开始")
    start = time.time()
    # async for 迭代异步可迭代对象
    async for data in async_data_generator(count):
        print(f"{name}处理异步数据: {data}")
    print(f"异步{name}结束总耗时: {time.time() - start:.2f}秒")


async def main():
    start = time.time()
    # 同时运行3个异步任务，每个任务迭代3次（每次等待1秒）
    await asyncio.gather(
        async_process("A", 3),
        async_process("B", 3),
        async_process("C", 3)
    )
    print(f"并发总耗时: {time.time() - start:.2f}秒")

if __name__ == '__main__':
    # 运行异步程序
    asyncio.run(main())