import requests
import sys
from PIL import Image


def simple_test(file_path, api_url="http://10.112.201.86:8099/api/holistic"):
    """简化版测试函数"""
    try:
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(api_url, files=files)

        if response.status_code == 200:
            result = response.json()
            print("成功!")
            print(f"结果: {result}")
            return result
        else:
            print(f"失败! 状态码: {response.status_code}")
            print(f"错误: {response.text}")
            return None

    except Exception as e:
        print(f"错误: {e}")
        return None


if __name__ == "__main__":
    # if len(sys.argv) != 2:
    #     print("用法: python simple_test.py <文件路径>")
    #     sys.exit(1)


    file_path = "/Users/alcuin/Downloads/test2.JPG"

    simple_test(file_path)