"""
家宽代理池使用示例
演示如何在 MediaCrawlerPro 中使用家宽代理池
"""
import asyncio
from pkg.proxy.proxy_ip_pool import create_ip_pool
from pkg.proxy.types import IpInfoModel
import httpx


async def example_1_basic_usage():
    """示例 1: 基础使用"""
    print("=" * 60)
    print("示例 1: 基础使用")
    print("=" * 60)

    # 创建代理池
    proxy_pool = await create_ip_pool(
        ip_pool_count=3,  # 获取 3 个代理
        enable_validate_ip=False,  # 不验证 IP（家宽代理池已经做了验证）
        ip_provider="home_proxy_pool"  # 使用家宽代理池
    )

    # 获取一个代理
    proxy_info: IpInfoModel = await proxy_pool.get_proxy()

    print(f"获取到代理:")
    print(f"  IP: {proxy_info.ip}")
    print(f"  端口: {proxy_info.port}")
    print(f"  协议: {proxy_info.protocol}")
    print(f"  用户名: {proxy_info.user}")
    print(f"  过期时间: {proxy_info.expired_time_ts}")

    # 格式化为 httpx 代理 URL
    proxy_url = proxy_info.format_httpx_proxy()
    print(f"  代理 URL: {proxy_url}")


async def example_2_use_with_httpx():
    """示例 2: 使用代理发起请求"""
    print("\n" + "=" * 60)
    print("示例 2: 使用代理发起请求")
    print("=" * 60)

    # 创建代理池
    proxy_pool = await create_ip_pool(
        ip_pool_count=2,
        enable_validate_ip=False,
        ip_provider="home_proxy_pool"
    )

    # 获取代理
    proxy_info: IpInfoModel = await proxy_pool.get_proxy()
    proxy_url = proxy_info.format_httpx_proxy()

    print(f"使用代理: {proxy_url}")

    # 使用代理发起请求
    try:
        async with httpx.AsyncClient(proxy=proxy_url, timeout=10.0) as client:
            response = await client.get("https://httpbin.org/ip")
            print(f"请求成功!")
            print(f"响应状态码: {response.status_code}")
            print(f"响应内容: {response.json()}")

    except Exception as e:
        print(f"请求失败: {e}")
        # 标记代理为无效
        await proxy_pool.mark_ip_invalid(proxy_info)
        print("已标记代理为无效")


async def example_3_multiple_requests():
    """示例 3: 使用多个代理发起请求"""
    print("\n" + "=" * 60)
    print("示例 3: 使用多个代理发起请求")
    print("=" * 60)

    # 创建代理池
    proxy_pool = await create_ip_pool(
        ip_pool_count=5,
        enable_validate_ip=False,
        ip_provider="home_proxy_pool"
    )

    # 发起多个请求
    urls = [
        "https://httpbin.org/ip",
        "https://httpbin.org/user-agent",
        "https://httpbin.org/headers",
    ]

    for i, url in enumerate(urls, 1):
        print(f"\n请求 {i}: {url}")

        # 获取代理
        try:
            proxy_info: IpInfoModel = await proxy_pool.get_proxy()
            proxy_url = proxy_info.format_httpx_proxy()

            print(f"  使用代理: {proxy_info.ip}:{proxy_info.port}")

            # 发起请求
            async with httpx.AsyncClient(proxy=proxy_url, timeout=10.0) as client:
                response = await client.get(url)
                print(f"  响应状态: {response.status_code}")

        except Exception as e:
            print(f"  请求失败: {e}")
            # 如果需要，标记代理无效
            # await proxy_pool.mark_ip_invalid(proxy_info)


async def example_4_retry_with_different_proxy():
    """示例 4: 使用不同代理重试失败的请求"""
    print("\n" + "=" * 60)
    print("示例 4: 使用不同代理重试失败的请求")
    print("=" * 60)

    # 创建代理池
    proxy_pool = await create_ip_pool(
        ip_pool_count=3,
        enable_validate_ip=False,
        ip_provider="home_proxy_pool"
    )

    url = "https://httpbin.org/delay/2"  # 延迟 2 秒的测试端点
    max_retries = 3

    for attempt in range(1, max_retries + 1):
        print(f"\n尝试 {attempt}/{max_retries}")

        try:
            # 获取新的代理
            proxy_info: IpInfoModel = await proxy_pool.get_proxy()
            proxy_url = proxy_info.format_httpx_proxy()

            print(f"  使用代理: {proxy_info.ip}:{proxy_info.port}")

            # 发起请求
            async with httpx.AsyncClient(proxy=proxy_url, timeout=5.0) as client:
                response = await client.get(url)

                if response.status_code == 200:
                    print(f"  ✓ 请求成功!")
                    print(f"  响应内容: {response.json()}")
                    break
                else:
                    print(f"  ✗ 请求失败: HTTP {response.status_code}")
                    # 标记代理失败
                    await proxy_pool.mark_ip_invalid(proxy_info)

        except Exception as e:
            print(f"  ✗ 请求异常: {e}")
            # 标记代理失败
            await proxy_pool.mark_ip_invalid(proxy_info)

        if attempt == max_retries:
            print(f"\n所有尝试均失败")


async def example_5_direct_api_call():
    """示例 5: 直接调用 API 获取代理"""
    print("\n" + "=" * 60)
    print("示例 5: 直接调用 API 获取代理")
    print("=" * 60)

    api_url = "http://localhost:8000/api/v1/home-proxy/proxy/get"

    # 获取代理
    async with httpx.AsyncClient() as client:
        response = await client.get(api_url)
        data = response.json()

        if data["code"] == 0:
            proxy_data = data["data"]
            print(f"获取到代理:")
            print(f"  代理 URL: {proxy_data['proxy']}")
            print(f"  Agent ID: {proxy_data['agent_id']}")
            print(f"  代理类型: {proxy_data['proxy_type']}")

            # 使用代理
            proxy_url = proxy_data["proxy"]
            agent_id = proxy_data["agent_id"]

            try:
                async with httpx.AsyncClient(proxy=proxy_url, timeout=10.0) as proxy_client:
                    test_response = await proxy_client.get("https://httpbin.org/ip")
                    print(f"\n使用代理请求成功:")
                    print(f"  {test_response.json()}")

            except Exception as e:
                print(f"\n请求失败: {e}")
                # 标记失败
                mark_failed_url = f"http://localhost:8000/api/v1/home-proxy/proxy/mark_failed"
                await client.post(mark_failed_url, params={"agent_id": agent_id})
                print(f"已标记 Agent {agent_id} 为失败")

        else:
            print(f"获取代理失败: {data['message']}")


async def example_6_integration_with_crawler():
    """示例 6: 集成到爬虫中使用"""
    print("\n" + "=" * 60)
    print("示例 6: 集成到爬虫中使用")
    print("=" * 60)

    # 模拟爬虫场景
    class SimpleCrawler:
        def __init__(self):
            self.proxy_pool = None

        async def init_proxy_pool(self):
            """初始化代理池"""
            self.proxy_pool = await create_ip_pool(
                ip_pool_count=5,
                enable_validate_ip=False,
                ip_provider="home_proxy_pool"
            )
            print("代理池已初始化")

        async def fetch_page(self, url: str) -> str:
            """获取页面内容"""
            max_retries = 3

            for attempt in range(1, max_retries + 1):
                try:
                    # 获取代理
                    proxy_info = await self.proxy_pool.get_proxy()
                    proxy_url = proxy_info.format_httpx_proxy()

                    print(f"  [尝试 {attempt}] 使用代理 {proxy_info.ip}:{proxy_info.port}")

                    # 发起请求
                    async with httpx.AsyncClient(proxy=proxy_url, timeout=10.0) as client:
                        response = await client.get(url)

                        if response.status_code == 200:
                            return response.text

                except Exception as e:
                    print(f"  [尝试 {attempt}] 失败: {e}")
                    # 标记代理失败
                    await self.proxy_pool.mark_ip_invalid(proxy_info)

            raise Exception(f"获取页面失败，已尝试 {max_retries} 次")

        async def crawl(self, urls: list):
            """爬取多个 URL"""
            for i, url in enumerate(urls, 1):
                print(f"\n爬取 {i}/{len(urls)}: {url}")
                try:
                    content = await self.fetch_page(url)
                    print(f"  ✓ 成功，内容长度: {len(content)} 字节")
                except Exception as e:
                    print(f"  ✗ 失败: {e}")

    # 使用爬虫
    crawler = SimpleCrawler()
    await crawler.init_proxy_pool()

    urls = [
        "https://httpbin.org/html",
        "https://httpbin.org/json",
    ]

    await crawler.crawl(urls)


async def main():
    """主函数"""
    print("家宽代理池使用示例\n")

    # 运行所有示例
    await example_1_basic_usage()
    await example_2_use_with_httpx()
    await example_3_multiple_requests()
    await example_4_retry_with_different_proxy()
    await example_5_direct_api_call()
    await example_6_integration_with_crawler()

    print("\n" + "=" * 60)
    print("所有示例运行完成!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
