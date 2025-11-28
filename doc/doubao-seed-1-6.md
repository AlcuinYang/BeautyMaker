部分大模型具备视觉理解能力，如当传入图片时，大模型可理解图片的信息，并结合这些信息完成如描述其中的物体等视觉相关任务。通过这篇教程，你可学习如何通过调用大模型 API 来识别传入图片里的信息。
<span id="31778cb5"></span>
# 支持模型
请参见[视觉理解](/docs/82379/1330310#ff5ef604)。
<span id="2ce4ac9b"></span>
# 前提条件
* [获取 API Key](https://console.volcengine.com/ark/region:ark+cn-beijing/apiKey) 
* [开通模型服务](https://console.volcengine.com/ark/openManagement)
* 在 [模型列表](/docs/82379/1330310) 获取所需 Model ID 
   * 通过 Endpoint ID 调用模型服务，请参考 [获取 Endpoint ID（创建自定义推理接入点）](/docs/82379/1099522)。

<span id="18cf565a"></span>
# 快速开始
支持视觉理解的大模型当前支持在请求中传入图片链接，图片信息需作为用户角色输入信息传给大模型，即`"role": "user"`。

```mixin-react
return (<Tabs>
<Tabs.TabPane title="图片理解" key="OkoUAdJM8k"><RenderMd content={`\`\`\`Python
import os
# Install SDK:  pip install 'volcengine-python-sdk[ark]'
from volcenginesdkarkruntime import Ark 

client = Ark(
    # The base URL for model invocation
    base_url="https://ark.cn-beijing.volces.com/api/v3", 
    # Get API Key：https://console.volcengine.com/ark/region:ark+cn-beijing/apikey
    api_key=os.getenv('ARK_API_KEY'), 
)

completion = client.chat.completions.create(
    # Replace with Model ID
    model = "doubao-seed-1-6-251015",
    messages = [
        {
            "role": "user",  
            "content": [   
                # 图片信息，希望模型理解的图片
                {"type": "image_url", "image_url": {"url":  "https://ark-project.tos-cn-beijing.volces.com/doc_image/ark_demo_img_1.png"},},
                # 文本消息，希望模型根据图片信息回答的问题
                {"type": "text", "text": "支持输入图片的模型系列是哪个？"}, 
            ],
        }
    ],
)

print(completion.choices[0].message.content)
\`\`\`

模型回复预览：
\`\`\`Shell
根据表格中的信息，支持输入图片的模型系列是 **Doubao-1.5-vision**。
\`\`\`

:::tip
提示词支持图片和文字混排，但图文顺序可能对模型的输出效果产生影响。在提示词构成为多张图片+1段文字，建议将文字放在提示词最后。
:::
`}></RenderMd></Tabs.TabPane></Tabs>);
 ```

<span id="f8d6cc48"></span>
# API 接口
<a href="https://www.volcengine.com/docs/82379/1494384">Chat API</a>
<span id="09d30d63"></span>
# 使用说明
:::tip
处理完图片/视频后，文件会从方舟服务器删除。方舟不会保留你提交的图片、视频以及文本信息等用户数据来训练模型。
:::
<span id="df962800"></span>
## 图片理解
<span id="4be57c22"></span>
### 图片传入方式
图片 URL 或 Base64 编码。用图片 URL 方式时，需确保图片 URL 可被访问。
:::tip
如果你希望获得更低的时延和成本，建议使用TOS（火山引擎对象存储）存储图片并生成访问链接。方舟与 TOS 网络打通，可使用内网通信，具备好处：

* 高速访问图片速度，降低模型回复的时延。
* 降低公网访问图片产生的流量费用。
:::
Chat API 是无状态的，如需模型对同一张图片进行多轮理解，则每次请求时都需传入该图片信息。
<span id="6412ed90"></span>
### 图片像素说明

1. 方舟在处理图片前会先行进行图片尺寸判断，如果图片超出下面的限制，会直接报错，传入图片满足下面条件（单位 px）：
   * 宽 > 14 且 高>14。
   * 宽*高范围： [196, 36,000,000]。
2. 满足上述条件的图片，方舟检测图片大小并将图片等比例压缩，并根据不同模式，将图片像素处理（等比例）至下面范围。
   * `detail:low`模式下，104万（1024×1024） px。
   * `detail:high`模式下，401万（2048×1960） px。
   其中，**detail** 字段控制理解图像精度，具体请参见[理解图像的深度控制](/docs/82379/1362931#bf4d9224)。

:::tip
对图片预处理，如裁剪/压缩图片，控制图片像素（`宽×高`）在104万（low）/ 401万（high）内，可降低模型响应时延与 token 消耗。
:::
<span id="8c5c16c8"></span>
### 图片数量说明
单次请求传入图片数量受限于模型上下文窗口。当输入过长，触发模型上下文窗口，信息会被截断。
> 模型上下文窗口请参见[模型列表](/docs/82379/1330310)。
> 举例说明：

> * 当图片总像素值大，使用的模型上下文窗口为 32k token，每张图片转为 1312  token ，单次请求可传入的图片数量为 `32000 ÷ 1312 = 24  `张。
> * 当图片总像素值小，使用的模型上下文窗口为 32k token，每张图片转为 256  token，单次请求可传入的数量为 `32000 ÷ 256 = 125` 张。

:::tip
模型回复的质量，受输入图片信息量影响。过多的图片会导致模型回复质量下滑，请合理控制单次请求传入图片的数量。
:::
<span id="7e6d3851"></span>
### 图片文件容量
单张图片小于 10 MB。
使用 base64 编码，请求体不可超过 64 MB。
<span id="f9ea084e"></span>
### token 用量说明
token 用量，根据图片宽高像素计算可得。图片转化 token 的公式为：
```Plain Text
min(image_width * image_hight ÷ 784, max_image_tokens)
```


* `detail:high`模式下，单图 token 限制(max_image_tokens)为 5120 token。
* `detail:low`模式下，单图 token 限制(max_image_tokens)为 1312 token。

图片尺寸为 `1280 px × 720 px`，即宽为 1280 px，高为 720 px，传入模型图片 token 限制为 1312，则理解这张图消耗的 token 为`1280×720÷784=1176`，因为小于 1312，消耗 token 数为 1176 。
图片尺寸为 `1920 px × 1080 px`，即宽为 1920 px，高为 1080 px，传入模型图片 token 限制为 1312，则理解这张图消耗的 token 为`1920×1080÷784=2645`，因为大于 1312，消耗 token 数为 1312 。这时会压缩 token，即图片的细节会丢失部分，譬如字体很小的图片，模型可能就无法准确识别文字内容。
<span id="5f46bf24"></span>
### 图片格式说明
支持的图片格式如下表，注意文件后缀匹配图片格式，即图片文件扩展名（URL传入时）、图片格式声明（Base64 编码传入时）需与图片实际信息一致。

   
   | | | | \
   |**图片格式** |**文件扩展名** |**内容格式** **Content Type** |\
   | | | |\
   | | |> * 上传文件至对象存储时设置，详情请参见[文档](https://www.volcengine.com/docs/6349/145523#%E8%AE%BE%E7%BD%AE%E6%96%87%E4%BB%B6%E5%85%83%E6%95%B0%E6%8D%AE)。 |\
   | | |> * [Base64 编码输入](/docs/82379/1362931#f6222fec) |\
   | | |> * 图片格式指定需使用小写 |
   |---|---|---|
   | | | | \
   |JPEG |.jpg, .jpeg |`image/jpeg` |
   | | | | \
   |PNG |.png |`image/png` |
   | | | | \
   |GIF |.gif |`image/gif` |
   | | | | \
   |WEBP |.webp |`image/webp` |
   | | | | \
   |BMP |.bmp |`image/bmp` |
   | | | | \
   |TIFF |.tiff, .tif |`image/tiff` |
   | | | | \
   |ICO |.ico |`image/ico` |
   | | | | \
   |DIB |.dib |`image/bmp` |
   | | | | \
   |ICNS |.icns |`image/icns` |
   | | | | \
   |SGI |.sgi |`image/sgi` |
   | | | | \
   |JPEG2000 |.j2c, .j2k, .jp2, .jpc, .jpf, .jpx |`image/jp2` |
   | | | | \
   |HEIC |\
   | |.heic |`image/heic` |\
   | | |> doubao-1.5-vision-pro及以后模型支持 |
   | | | | \
   |HEIF |\
   | |.heif |`image/heif` |\
   | | |> doubao-1.5-vision-pro及以后模型支持 |


:::tip
TIFF、 SGI、ICNS、JPEG2000 几种格式图片，需保证和元数据对齐，如在对象存储中正确设置文件元数据，否则会解析失败，详细请参见 [使用视觉理解模型时，报错InvalidParameter？](/docs/82379/1359411#effccb14)
:::
<span id="8c9039b9"></span>
### API 参数字段说明
以下字段视觉理解暂不支持。

* 不支持设置频率惩罚系数，无 **frequency_penalty** 字段。
* 不支持设置存在惩罚系数，**presence_penalty** 字段。
* 不支持为单个请求生成多个返回，无 **n** 字段。

<span id="547c81e8"></span>
# 使用示例
<span id="d86010f4"></span>
## 多图输入
API 可支持接受和处理多个图像输入，这些图像可通过图片可访问 URL 或图片转为 Base64 编码后输入，模型将结合所有传入的图像中的信息来回答问题。

```mixin-react
return (<Tabs>
<Tabs.TabPane title="Curl" key="YtPXUrZQ3t"><RenderMd content={`\`\`\`Shell
curl https://ark.cn-beijing.volces.com/api/v3/chat/completions \\
   -H "Content-Type: application/json"  \\
   -H "Authorization: Bearer $ARK_API_KEY"  \\
   -d '{
    "model": "doubao-seed-1-6-251015",
    "messages": [
        {
            "role": "user",
            "content": [                
                {"type": "image_url","image_url": {"url":  "https://ark-project.tos-cn-beijing.volces.com/doc_image/ark_demo_img_1.png"}},
                {"type": "image_url","image_url": {"url":  "https://ark-project.tos-cn-beijing.volces.com/doc_image/ark_demo_img_2.png"}},
                {"type": "text", "text": "支持输入图片的模型系列是哪个？同时，豆包应用场景有哪些？"}
            ]
        }
    ],
    "max_tokens": 300
  }'
\`\`\`


* 按需替换 Model ID，查询 Model ID 参见 [模型列表](/docs/82379/1330310)。
`}></RenderMd></Tabs.TabPane>
<Tabs.TabPane title="Python" key="nU8nDPD26j"><RenderMd content={`\`\`\`Python
import os
# Install SDK:  pip install 'volcengine-python-sdk[ark]'
from volcenginesdkarkruntime import Ark 

client = Ark(
    # The base URL for model invocation
    base_url="https://ark.cn-beijing.volces.com/api/v3", 
    # Get API Key：https://console.volcengine.com/ark/region:ark+cn-beijing/apikey
    api_key=os.getenv('ARK_API_KEY'), 
)

completion = client.chat.completions.create(
    # Replace with Model ID
    model = "doubao-seed-1-6-251015",
    messages=[
        {
            "role": "user",
            "content": [                
                {"type": "image_url","image_url": {"url":  "https://ark-project.tos-cn-beijing.volces.com/doc_image/ark_demo_img_1.png"}},
                {"type": "image_url","image_url": {"url":  "https://ark-project.tos-cn-beijing.volces.com/doc_image/ark_demo_img_2.png"}},
                {"type": "text", "text": "支持输入图片的模型系列是哪个？同时，豆包应用场景有哪些？"},
            ],
        }
    ],
)

print(completion.choices[0])
\`\`\`

`}></RenderMd></Tabs.TabPane>
<Tabs.TabPane title="Go" key="LJDwKphlxC"><RenderMd content={`\`\`\`Go
package main

import (
    "context"
    "fmt"
    "os"
    "github.com/volcengine/volcengine-go-sdk/service/arkruntime"
    "github.com/volcengine/volcengine-go-sdk/service/arkruntime/model"
    "github.com/volcengine/volcengine-go-sdk/volcengine"
)

func main() {
    client := arkruntime.NewClientWithApiKey(
        //通过 os.Getenv 从环境变量中获取 ARK_API_KEY
        os.Getenv("ARK_API_KEY"),
        // The base URL for model invocation
        arkruntime.WithBaseUrl("https://ark.cn-beijing.volces.com/api/v3"),
    )
    // 创建一个上下文，通常用于传递请求的上下文信息，如超时、取消等
    ctx := context.Background()
    // 构建消息内容：包含两张图片URL和一段文本
    contentParts := []*model.ChatCompletionMessageContentPart{
        // 第一张图片
        {
            Type: "image_url",
            ImageURL: &model.ChatMessageImageURL{
                URL: "https://ark-project.tos-cn-beijing.volces.com/doc_image/ark_demo_img_1.png",
            },
        },
        // 第二张图片
        {
            Type: "image_url",
            ImageURL: &model.ChatMessageImageURL{
                URL: "https://ark-project.tos-cn-beijing.volces.com/doc_image/ark_demo_img_2.png",
            },
        },
        // 文本内容
        {
            Type: "text",
            Text: "支持输入图片的模型系列是哪个？同时，豆包应用场景有哪些？",
        },
    }
    // 构建聊天完成请求，设置请求的模型和消息内容
    req := model.CreateChatCompletionRequest{
        // Replace with Model ID
       Model: "doubao-seed-1-6-251015",
       Messages: []*model.ChatCompletionMessage{
          {
             // 消息的角色为用户
             Role: model.ChatMessageRoleUser,
             Content: &model.ChatCompletionMessageContent{
                ListValue: contentParts, // 多类型内容使用ListValue
             },
          },
       },
       MaxTokens: volcengine.Int(300), // 设置模型输出最大 token 数
    }

    // 发送聊天完成请求，并将结果存储在 resp 中，将可能出现的错误存储在 err 中
    resp, err := client.CreateChatCompletion(ctx, req)
    if err!= nil {
       // 若出现错误，打印错误信息并终止程序
       fmt.Printf("standard chat error: %v\\n", err)
       return
    }
    // 打印聊天完成请求的响应结果
    fmt.Println(*resp.Choices[0].Message.Content.StringValue)
}
\`\`\`

`}></RenderMd></Tabs.TabPane>
<Tabs.TabPane title="Java" key="wFKf8Aa3hx"><RenderMd content={`\`\`\`Java
package com.ark.sample;

import com.volcengine.ark.runtime.model.completion.chat.*;
import com.volcengine.ark.runtime.model.completion.chat.ChatCompletionContentPart.*;
import com.volcengine.ark.runtime.service.ArkService;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.TimeUnit;
import okhttp3.ConnectionPool;
import okhttp3.Dispatcher;

public class MultiImageSample {
  static String apiKey = System.getenv("ARK_API_KEY");
  static ConnectionPool connectionPool = new ConnectionPool(5, 1, TimeUnit.SECONDS);
  static Dispatcher dispatcher = new Dispatcher();
  static ArkService service = ArkService.builder()
       .dispatcher(dispatcher)
       .connectionPool(connectionPool)
       .baseUrl("https://ark.cn-beijing.volces.com/api/v3") // The base URL for model invocation
       .apiKey(apiKey)
       .build();

  public static void main(String[] args) throws Exception {

    List<ChatMessage> messagesForReqList = new ArrayList<>();

    // 构建消息内容
    List<ChatCompletionContentPart> contentParts = new ArrayList<>();

    // 第一张图片部分使用builder模式
    contentParts.add(ChatCompletionContentPart.builder()
         .type("image_url")
         .imageUrl(new ChatCompletionContentPartImageURL(
            "https://ark-project.tos-cn-beijing.volces.com/doc_image/ark_demo_img_1.png"))
         .build());

    // 第二张图片部分使用builder模式
    contentParts.add(ChatCompletionContentPart.builder()
         .type("image_url")
         .imageUrl(new ChatCompletionContentPartImageURL(
            "https://ark-project.tos-cn-beijing.volces.com/doc_image/ark_demo_img_2.png"))
         .build());

    contentParts.add(ChatCompletionContentPart.builder()
         .type("text")
         .text("支持输入图片的模型系列是哪个？同时，豆包应用场景有哪些？")
         .build());

    messagesForReqList.add(ChatMessage.builder()
         .role(ChatMessageRole.USER)
         .multiContent(contentParts)
         .build());

    ChatCompletionRequest req = ChatCompletionRequest.builder()
         .model("doubao-seed-1-6-251015") //Replace with Model ID
         .messages(messagesForReqList)
         .maxTokens(300)
         .build();

    service.createChatCompletion(req)
         .getChoices()
         .forEach(choice -> System.out.println(choice.getMessage().getContent()));
    // shutdown service after all requests are finished
    service.shutdownExecutor();
  }
}
\`\`\`

`}></RenderMd></Tabs.TabPane></Tabs>);
 ```


<span id="f6222fec"></span>
## Base64 编码输入
如果你要传入的图片/视频在本地，你可将其转化为 Base64 编码，然后提交给大模型。下面是一个简单的示例代码。
:::warning
传入 Base64 编码格式时，请遵循以下规则：

* 格式遵循 `data:image/<IMAGE_FORMAT>;base64,<BASE64_ENCODING>`，其中，
   * 图片格式：`jpeg`、`png`、`gif`等，支持的图片格式详细见[图片格式说明](/docs/82379/1362931#5f46bf24)。
   * Base64 编码：图片的 Base64 编码。
:::

```mixin-react
return (<Tabs>
<Tabs.TabPane title="Curl" key="tY8jhpyJ2G"><RenderMd content={`\`\`\`Shell
BASE64_IMAGE=$(base64 < path_to_your_image.jpeg) && curl https://ark.cn-beijing.volces.com/api/v3/chat/completions \\
   -H "Content-Type: application/json"  \\
   -H "Authorization: Bearer $ARK_API_KEY"  \\
   -d @- <<EOF
   {
    "model": "doubao-seed-1-6-251015",
    "messages": [
      {
        "role": "user",
        "content": [
          {
            "type": "image_url",
            "image_url": {
              "url": "data:image/jpeg;base64,$BASE64_IMAGE"
            }
          },
          {
            "type": "text",
            "text": "图里有什么"
          }
        ]
      }
    ],
    "max_tokens": 300
  }
EOF
\`\`\`


* 按需替换 Model ID，查询 Model ID 参见 [模型列表](/docs/82379/1330310)。
`}></RenderMd></Tabs.TabPane>
<Tabs.TabPane title="Python" key="BLMqfxLah7"><RenderMd content={`\`\`\`Python
import base64
import os
# Install SDK:  pip install 'volcengine-python-sdk[ark]'
from volcenginesdkarkruntime import Ark 

client = Ark(
    # The base URL for model invocation
    base_url="https://ark.cn-beijing.volces.com/api/v3", 
    # Get API Key：https://console.volcengine.com/ark/region:ark+cn-beijing/apikey
    api_key=os.getenv('ARK_API_KEY'), 
)

# 定义方法将指定路径图片转为Base64编码
def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')

# 需传给大模型的图片
image_path = "path_to_your_image.jpg"

# 将图片转为Base64编码
base64_image = encode_image(image_path)

completion = client.chat.completions.create(
  # Replace with Model ID
  model = "doubao-seed-1-6-251015",
  messages=[
    {
      "role": "user",
      "content": [
        {
          "type": "image_url",
          "image_url": {
          # 需注意：传入Base64编码遵循格式 data:image/<IMAGE_FORMAT>;base64,{base64_image}：
          # PNG图片："url":  f"data:image/png;base64,{base64_image}"
          # JPEG图片："url":  f"data:image/jpeg;base64,{base64_image}"
          # WEBP图片："url":  f"data:image/webp;base64,{base64_image}"
            "url":  f"data:image/<IMAGE_FORMAT>;base64,{base64_image}"
          },         
        },
        {
          "type": "text",
          "text": "图里有什么",
        },
      ],
    }
  ],
)

print(completion.choices[0])
\`\`\`

`}></RenderMd></Tabs.TabPane>
<Tabs.TabPane title="Go" key="mAvq2uUFE6"><RenderMd content={`\`\`\`Go
package main

import (
    "context"
    "encoding/base64"
    "fmt"
    "os"
    "github.com/volcengine/volcengine-go-sdk/service/arkruntime"
    "github.com/volcengine/volcengine-go-sdk/service/arkruntime/model"
    "github.com/volcengine/volcengine-go-sdk/volcengine"
)

func main() {
    // 读取本地图片文件
    imageBytes, err := os.ReadFile("path_to_your_image.jpeg") // 替换为实际图片路径
    if err != nil {
        fmt.Printf("读取图片失败: %v\\n", err)
        return
    }
    base64Image := base64.StdEncoding.EncodeToString(imageBytes)

    client := arkruntime.NewClientWithApiKey(
        os.Getenv("ARK_API_KEY"),
        // The base URL for model invocation  .
        arkruntime.WithBaseUrl("https://ark.cn-beijing.volces.com/api/v3"),
        )
    ctx := context.Background()
    req := model.CreateChatCompletionRequest{
        // Replace with Model ID
        Model: "doubao-seed-1-6-251015",
        Messages: []*model.ChatCompletionMessage{
            {
                Role: "user",
                Content: &model.ChatCompletionMessageContent{
                    ListValue: []*model.ChatCompletionMessageContentPart{
                        {
                            Type: "image_url",
                            ImageURL: &model.ChatMessageImageURL{
                                URL: fmt.Sprintf("data:image/jpeg;base64,%s", base64Image),
                            },
                        },
                        {
                            Type: "text",
                            Text: "图片主要讲了什么?",
                        },
                    },
                },
            },
        },
    }

    resp, err := client.CreateChatCompletion(ctx, req)
    if err != nil {
        fmt.Printf("standard chat error: %v\\n", err)
        return
    }
    fmt.Println(*resp.Choices[0].Message.Content.StringValue)
}
\`\`\`

`}></RenderMd></Tabs.TabPane>
<Tabs.TabPane title="Java" key="yWF6CYODCM"><RenderMd content={`\`\`\`Java
package com.ark.sample;

import com.volcengine.ark.runtime.model.completion.chat.*;
import com.volcengine.ark.runtime.model.completion.chat.ChatCompletionContentPart.*;
import com.volcengine.ark.runtime.service.ArkService;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.TimeUnit;
import okhttp3.ConnectionPool;
import okhttp3.Dispatcher;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Base64;
import java.io.IOException;

public class Sample {
    static String apiKey = System.getenv("ARK_API_KEY");
    static ConnectionPool connectionPool = new ConnectionPool(5, 1, TimeUnit.SECONDS);
    static Dispatcher dispatcher = new Dispatcher();
    static ArkService service = ArkService.builder()
         .dispatcher(dispatcher)
         .connectionPool(connectionPool)
         .baseUrl("https://ark.cn-beijing.volces.com/api/v3") // The base URL for model invocation  .
         .apiKey(apiKey)
         .build();

    // Base64编码方法
    private static String encodeImage(String imagePath) throws IOException {
        byte[] imageBytes = Files.readAllBytes(Path.of(imagePath));
        return Base64.getEncoder().encodeToString(imageBytes);
    }

    public static void main(String[] args) throws Exception {

        List<ChatMessage> messagesForReqList = new ArrayList<>();

        // 本地图片路径（替换为实际路径）
        String imagePath = "/Users/bytedance/workspace/ark_vlm/image/image.jpeg";

        // 生成Base64数据URL
        String base64Data = "data:image/jpeg;base64," + encodeImage(imagePath);

        // 构建消息内容（修复内容部分构建方式）
        List<ChatCompletionContentPart> contentParts = new ArrayList<>();

        // 图片部分使用builder模式
        contentParts.add(ChatCompletionContentPart.builder()
                 .type("image_url")
                 .imageUrl(new ChatCompletionContentPartImageURL(base64Data))
                 .build());

        // 文本部分使用builder模式
        contentParts.add(ChatCompletionContentPart.builder()
                 .type("text")
                 .text("图里有什么")
                 .build());

        // 创建消息
        messagesForReqList.add(ChatMessage.builder()
                 .role(ChatMessageRole.USER)
                 .multiContent(contentParts)
                 .build());

        ChatCompletionRequest req = ChatCompletionRequest.builder()
                 .model("doubao-seed-1-6-251015") //Replace with Model ID  .
                 .messages(messagesForReqList)
                 .maxTokens(300)
                 .build();

        service.createChatCompletion(req)
                 .getChoices()
                 .forEach(choice -> System.out.println(choice.getMessage().getContent()));
        // shutdown service after all requests are finished
        service.shutdownExecutor();
    }
}
\`\`\`

`}></RenderMd></Tabs.TabPane></Tabs>);
 ```


<span id="bf4d9224"></span>
## 控制图片理解的精细度
控制图片理解的精细度（指对画面的精细）： **image_pixel_limit 、detail** 字段，2个字段若同时配置，则生效逻辑如下：

* 生效前提：图片像素范围在 [196, 36,000,000] px，否则直接报错。
* 生效优先级：**image_pixel_limit** 高于 **detail** 字段，即同时配置 **detail** 与 **image_pixel_limit** 字段时，生效 **image_pixel_limit** 字段配置。
* 缺省时生效：**image_pixel_limit** 字段的 **min_pixels** / **max_pixels** 字段未设置，则使用 **detail** （默认值为`low`）配置所对应的值。
   * **detail**为`low`**：min_pixels** 值`3136` **；max_pixels** 值`1048576`。
   * **detail**为`high`**：min_pixels** 值`3136` **；max_pixels** 值`4014080`。

下面分别介绍如何通过 **detail** 、 **image_pixel_limit** 控制视觉理解的精度。
<span id="885d96dc"></span>
### 通过 detail 字段（图片理解）
你可通过`detail`参数来控制模型理解图片的精细度，返回速度，token用量，计费公式请参见[token 用量说明](/docs/82379/1362931#f9ea084e)。

* `low`：“低分辨率”模式，默认此模式，处理速度会提高，适合图片本身细节较少或者只需模型理解图片大致信息或者对速度有要求的场景。此时 **min_pixels** 取值`3136`、**max_pixels** 取值`1048576`。不在此范围且小于3600w px的图片，方舟会等比例缩放至范围内。
* `high`：“高分辨率”模式，模型可感知图片更多的细节，但是处理图片速度会降低，适合图像像素值高且需关注细节信息的场景，如街道地图分析等。此时 **min_pixels** 取值`3136`、**max_pixels** 取值`4014080`。不在此范围且小于3600w px的图片，方舟会等比例缩放至范围内。


```mixin-react
return (<Tabs>
<Tabs.TabPane title="Curl" key="Hr2Ben4Yyu"><RenderMd content={`\`\`\`Shell
curl https://ark.cn-beijing.volces.com/api/v3/chat/completions \\
   -H "Content-Type: application/json" \\
   -H "Authorization: Bearer $ARK_API_KEY" \\
   -d '{
    "model": "doubao-seed-1-6-251015",
    "messages": [
        {
            "role": "user",
            "content": [                
                {"type": "image_url","image_url": {"url":  "https://ark-project.tos-cn-beijing.volces.com/doc_image/ark_demo_img_1.png"},"detail": "high"},
                {"type": "text", "text": "支持输入图片的模型系列是哪个？"}
            ]
        }
    ],
    "max_tokens": 300
  }'
\`\`\`


* 按需替换 Model ID，查询 Model ID 参见 [模型列表](/docs/82379/1330310)。
`}></RenderMd></Tabs.TabPane>
<Tabs.TabPane title="Python" key="tQ4USeisGW"><RenderMd content={`\`\`\`Python
import os
# Install SDK:  pip install 'volcengine-python-sdk[ark]'
from volcenginesdkarkruntime import Ark 

client = Ark(
    # The base URL for model invocation
    base_url="https://ark.cn-beijing.volces.com/api/v3", 
    # Get API Key：https://console.volcengine.com/ark/region:ark+cn-beijing/apikey
    api_key=os.getenv('ARK_API_KEY'), 
)

completion = client.chat.completions.create(
    # Replace with Model ID
    model = "doubao-seed-1-6-251015",
    messages=[
        {
            "role": "user",
            "content": [                
                {"type": "image_url","image_url": {"url":  "https://ark-project.tos-cn-beijing.volces.com/doc_image/ark_demo_img_1.png"},"detail": "high"},
                {"type": "text", "text": "支持输入图片的模型系列是哪个？"},
            ],
        }
    ],
)

print(completion.choices[0])
\`\`\`

`}></RenderMd></Tabs.TabPane>
<Tabs.TabPane title="Go" key="uuiFQYnR1w"><RenderMd content={`\`\`\`Go
package main

import (
    "context"
    "fmt"
    "os"
    "github.com/volcengine/volcengine-go-sdk/service/arkruntime"
    "github.com/volcengine/volcengine-go-sdk/service/arkruntime/model"
    "github.com/volcengine/volcengine-go-sdk/volcengine"
)

func main() {
    client := arkruntime.NewClientWithApiKey(
        //通过 os.Getenv 从环境变量中获取 ARK_API_KEY
        os.Getenv("ARK_API_KEY"),
        // The base URL for model invocation
        arkruntime.WithBaseUrl("https://ark.cn-beijing.volces.com/api/v3"),
    )
    // 创建一个上下文，通常用于传递请求的上下文信息，如超时、取消等
    ctx := context.Background()
    // 构建消息内容：包含两张图片URL和一段文本
    contentParts := []*model.ChatCompletionMessageContentPart{
        // 第一张图片
        {
            Type: "image_url",
            ImageURL: &model.ChatMessageImageURL{
                URL: "https://ark-project.tos-cn-beijing.volces.com/doc_image/ark_demo_img_1.png",
                Detail: model.ImageURLDetailHigh,
            },
        },
        // 文本内容
        {
            Type: "text",
            Text: "支持输入图片的模型系列是哪个？",
        },
    }
    // 构建聊天完成请求，设置请求的模型和消息内容
    req := model.CreateChatCompletionRequest{
        // Replace with Model ID
       Model: "doubao-seed-1-6-251015",
       Messages: []*model.ChatCompletionMessage{
          {
             // 消息的角色为用户
             Role: model.ChatMessageRoleUser,
             Content: &model.ChatCompletionMessageContent{
                ListValue: contentParts, // 多类型内容使用ListValue
             },
          },
       },
       MaxTokens: volcengine.Int(300), // 设置模型输出最大 token 数
    }

    // 发送聊天完成请求，并将结果存储在 resp 中，将可能出现的错误存储在 err 中
    resp, err := client.CreateChatCompletion(ctx, req)
    if err!= nil {
       // 若出现错误，打印错误信息并终止程序
       fmt.Printf("standard chat error: %v\\n", err)
       return
    }
    // 打印聊天完成请求的响应结果
    fmt.Println(*resp.Choices[0].Message.Content.StringValue)
}
\`\`\`

`}></RenderMd></Tabs.TabPane>
<Tabs.TabPane title="Java" key="GZKLDH0ouf"><RenderMd content={`\`\`\`Java
package com.ark.sample;

import com.volcengine.ark.runtime.model.completion.chat.*;
import com.volcengine.ark.runtime.model.completion.chat.ChatCompletionContentPart.*;
import com.volcengine.ark.runtime.service.ArkService;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.TimeUnit;
import okhttp3.ConnectionPool;
import okhttp3.Dispatcher;

public class MultiImageSample {
  static String apiKey = System.getenv("ARK_API_KEY");
  static ConnectionPool connectionPool = new ConnectionPool(5, 1, TimeUnit.SECONDS);
  static Dispatcher dispatcher = new Dispatcher();
  static ArkService service = ArkService.builder()
       .dispatcher(dispatcher)
       .connectionPool(connectionPool)
       .baseUrl("https://ark.cn-beijing.volces.com/api/v3")  // The base URL for model invocation  .
       .apiKey(apiKey)
       .build();

  public static void main(String[] args) throws Exception {

    List<ChatMessage> messagesForReqList = new ArrayList<>();

    // 构建消息内容
    List<ChatCompletionContentPart> contentParts = new ArrayList<>();

    // 第一张图片部分使用builder模式
    contentParts.add(ChatCompletionContentPart.builder()
         .type("image_url")
         .imageUrl(new ChatCompletionContentPartImageURL(
            "https://ark-project.tos-cn-beijing.volces.com/doc_image/ark_demo_img_1.png","high"))
         .build());

    // 文本部分使用builder模式
    contentParts.add(ChatCompletionContentPart.builder()
         .type("text")
         .text("支持输入图片的模型系列是哪个？")
         .build());

    // 创建消息
    messagesForReqList.add(ChatMessage.builder()
         .role(ChatMessageRole.USER)
         .multiContent(contentParts)
         .build());

    ChatCompletionRequest req = ChatCompletionRequest.builder()
         .model("doubao-seed-1-6-251015") //Replace with Model ID  .
         .messages(messagesForReqList)
         .maxTokens(300)
         .build();

    service.createChatCompletion(req)
         .getChoices()
         .forEach(choice -> System.out.println(choice.getMessage().getContent()));
    // shutdown service after all requests are finished
    service.shutdownExecutor();
  }
}
\`\`\`

`}></RenderMd></Tabs.TabPane></Tabs>);
 ```

<span id="d2b576dd"></span>
### **通过 image_pixel_limit 结构体**
控制传入给方舟的图像像素大小范围，如果不在此范围，则会等比例放大或者缩小至该范围内，后传给模型进行理解。你可通过 **image_pixel_limit** 结构体，精细控制模型可理解的图片像素多少。
对应结构体如下：
```Bash
"image_pixel_limit": {
    "max_pixels": 3014080,   # 图片最大像素
    "min_pixels": 3136       # 图片最小像素
}
```

示例代码如下：
> Java SDK、 Go SDK 不支持此字段。


```mixin-react
return (<Tabs>
<Tabs.TabPane title="Curl" key="oVlifybgH4"><RenderMd content={`\`\`\`Shell
curl https://ark.cn-beijing.volces.com/api/v3/chat/completions \\
   -H "Content-Type: application/json" \\
   -H "Authorization: Bearer $ARK_API_KEY" \\
   -d '{
    "model": "doubao-seed-1-6-251015",
    "messages": [
        {
            "role": "user",
            "content": [                
                {"type": "image_url","image_url": {"url":  "https://ark-project.tos-cn-beijing.volces.com/doc_image/ark_demo_img_1.png"},"image_pixel_limit": {"max_pixels": 3014080,"min_pixels": 3136}},
                {"type": "text", "text": "支持输入图片的模型系列是哪个？"}
            ]
        }
    ],
    "max_tokens": 300
  }'
\`\`\`


* 按需替换 Model ID，查询 Model ID 参见 [模型列表](/docs/82379/1330310)。
`}></RenderMd></Tabs.TabPane>
<Tabs.TabPane title="Python" key="wI15o6W23B"><RenderMd content={`\`\`\`Python
import os
# Install SDK: pip install 'volcengine-python-sdk[ark]'
from volcenginesdkarkruntime import Ark 

client = Ark(
    # The base URL for model invocation
    base_url="https://ark.cn-beijing.volces.com/api/v3", 
    # Get API Key：https://console.volcengine.com/ark/region:ark+cn-beijing/apikey
    api_key=os.getenv('ARK_API_KEY'), 
)

completion = client.chat.completions.create(
    # Replace with Model ID
    model = "doubao-seed-1-6-251015",
    messages=[
        {
            # 消息角色为用户
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    # 第一张图片链接及细节设置为 high
                    "image_url": {
                        # 你可替换图片链接为你的实际图片链接
                        "url":  "https://ark-project.tos-cn-beijing.volces.com/doc_image/ark_demo_img_1.png",
                        "image_pixel_limit": {
                            "max_pixels": 3014080,
                            "min_pixels": 3136,
                        },
                    },
                 },
                # 文本类型的消息内容，询问图片里有什么
                {"type": "text", "text": "支持输入图片的模型系列是哪个？"},
            ],
        }
    ],
)

print(completion.choices[0])
\`\`\`

`}></RenderMd></Tabs.TabPane></Tabs>);
 ```


<span id="474e4601"></span>
## 图文混排
支持灵活地传入提示词和图片信息的方式，你可任意调整传图图片和文本的顺序，以及在`system message`或者`User message`传入图文信息。模型会根据顺序返回处理信息的结果，示例如下。

```mixin-react
return (<Tabs>
<Tabs.TabPane title="Curl" key="R15Bo4pX3O"><RenderMd content={`\`\`\`Shell
curl https://ark.cn-beijing.volces.com/api/v3/chat/completions \\
   -H "Content-Type: application/json" \\
   -H "Authorization: Bearer $ARK_API_KEY" \\
   -d '{
    "model": "doubao-seed-1-6-251015",
    "messages": [
        {
            "role": "system",
            "content": [
                {"type": "text", "text": "下面人物是目标人物"},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://ark-project.tos-cn-beijing.volces.com/doc_image/target.png"
                    }
                },
                {"type": "text", "text": "请确认下面图片中是否含有目标人物"}
            ]
        },
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "图片1中是否含有目标人物"},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://ark-project.tos-cn-beijing.volces.com/doc_image/scene_01.png"
                    }
                },
                {"type": "text", "text": "图片2中是否含有目标人物"},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://ark-project.tos-cn-beijing.volces.com/doc_image/scene_02.png"
                    }
                }
            ]
        }
    ],
    "max_tokens": 300
  }'
\`\`\`


* 按需替换 Model ID，查询 Model ID 参见 [模型列表](/docs/82379/1330310)。
`}></RenderMd></Tabs.TabPane>
<Tabs.TabPane title="Python" key="RGN8NYuVAT"><RenderMd content={`\`\`\`Python
import os
# Install SDK:  pip install 'volcengine-python-sdk[ark]'
from volcenginesdkarkruntime import Ark 

client = Ark(
    # The base URL for model invocation
    base_url="https://ark.cn-beijing.volces.com/api/v3", 
    # Get API Key：https://console.volcengine.com/ark/region:ark+cn-beijing/apikey
    api_key=os.getenv('ARK_API_KEY'), 
)

completion = client.chat.completions.create(
    # Replace with Model ID
    model = "doubao-seed-1-6-251015",
    messages=[
        {
            "role": "system",
            "content": [
                {"type": "text", "text": "下面人物是目标人物"},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://ark-project.tos-cn-beijing.volces.com/doc_image/target.png"
                    },
                },
                {"type": "text", "text": "请确认下面图片中是否含有目标人物"},
            ],
        },
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "图片1中是否含有目标人物"},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://ark-project.tos-cn-beijing.volces.com/doc_image/scene_01.png"
                    },
                },
                {"type": "text", "text": "图片2中是否含有目标人物"},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://ark-project.tos-cn-beijing.volces.com/doc_image/scene_02.png"
                    },
                },
            ],
        },
    ],
)


print(completion.choices[0].message.content)
\`\`\`

`}></RenderMd></Tabs.TabPane>
<Tabs.TabPane title="Go" key="n2Xho6NNS0"><RenderMd content={`\`\`\`Go
package main

import (
    "context"
    "fmt"
    "os"
    "github.com/volcengine/volcengine-go-sdk/service/arkruntime"
    "github.com/volcengine/volcengine-go-sdk/service/arkruntime/model"
    "github.com/volcengine/volcengine-go-sdk/volcengine"
)

func main() {
    client := arkruntime.NewClientWithApiKey(
        // Get API Key：https://console.volcengine.com/ark/region:ark+cn-beijing/apikey
        os.Getenv("ARK_API_KEY"),
        // The base URL for model invocation
        arkruntime.WithBaseUrl("https://ark.cn-beijing.volces.com/api/v3"),
    )
    // 创建一个上下文，通常用于传递请求的上下文信息，如超时、取消等
  ctx := context.Background()

  // 构建system消息内容
  systemContentParts := []*model.ChatCompletionMessageContentPart{
    // 文本内容
    {
      Type: "text",
      Text: "下面人物是目标人物",
    },
    // 目标人物图片
    {
      Type: "image_url",
      ImageURL: &model.ChatMessageImageURL{
        URL: "https://ark-project.tos-cn-beijing.volces.com/doc_image/target.png",
      },
    },
    // 文本内容
    {
      Type: "text",
      Text: "请确认下面图片中是否含有目标人物",
    },
  }

  // 构建user消息内容
  userContentParts := []*model.ChatCompletionMessageContentPart{
    // 文本内容
    {
      Type: "text",
      Text: "图片1中是否含有目标人物",
    },
    // 第一张场景图片
    {
      Type: "image_url",
      ImageURL: &model.ChatMessageImageURL{
        URL: "https://ark-project.tos-cn-beijing.volces.com/doc_image/scene_01.png",
      },
    },
    // 文本内容
    {
      Type: "text",
      Text: "图片2中是否含有目标人物",
    },
    // 第二张场景图片
    {
      Type: "image_url",
      ImageURL: &model.ChatMessageImageURL{
        URL: "https://ark-project.tos-cn-beijing.volces.com/doc_image/scene_02.png",
      },
    },
  }

  // 构建聊天完成请求，设置请求的模型和消息内容
  req := model.CreateChatCompletionRequest{
    // Replace with Model ID
    Model: "doubao-seed-1-6-251015",
    Messages: []*model.ChatCompletionMessage{
      {
        // 消息的角色为system
        Role: model.ChatMessageRoleSystem,
        Content: &model.ChatCompletionMessageContent{
          ListValue: systemContentParts, // 多类型内容使用ListValue
        },
      },
      {
        // 消息的角色为user
        Role: model.ChatMessageRoleUser,
        Content: &model.ChatCompletionMessageContent{
          ListValue: userContentParts, // 多类型内容使用ListValue
        },
      },
    },
    MaxTokens: volcengine.Int(300), // 设置模型输出最大 token 数
  }

    // 发送聊天完成请求，并将结果存储在 resp 中，将可能出现的错误存储在 err 中
    resp, err := client.CreateChatCompletion(ctx, req)
    if err!= nil {
       // 若出现错误，打印错误信息并终止程序
       fmt.Printf("standard chat error: %v\\n", err)
       return
    }
    // 打印聊天完成请求的响应结果
    fmt.Println(*resp.Choices[0].Message.Content.StringValue)
}
\`\`\`

`}></RenderMd></Tabs.TabPane>
<Tabs.TabPane title="Java" key="mKuiTUi3Pl"><RenderMd content={`\`\`\`Java
package com.ark.sample;

import com.volcengine.ark.runtime.model.completion.chat.*;
import com.volcengine.ark.runtime.model.completion.chat.ChatCompletionContentPart.*;
import com.volcengine.ark.runtime.service.ArkService;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.TimeUnit;
import okhttp3.ConnectionPool;
import okhttp3.Dispatcher;

public class MultiImageSample {
  static String apiKey = System.getenv("ARK_API_KEY");
  static ConnectionPool connectionPool = new ConnectionPool(5, 1, TimeUnit.SECONDS);
  static Dispatcher dispatcher = new Dispatcher();
  static ArkService service = ArkService.builder()
       .dispatcher(dispatcher)
       .connectionPool(connectionPool)
       .baseUrl("https://ark.cn-beijing.volces.com/api/v3")  // The base URL for model invocation
       .apiKey(apiKey)
       .build();

  public static void main(String[] args) throws Exception {
    List<ChatMessage> messagesForReqList = new ArrayList<>();
    
    // 构建system消息内容
    List<ChatCompletionContentPart> systemContentParts = new ArrayList<>();
    systemContentParts.add(ChatCompletionContentPart.builder()
         .type("text")
         .text("下面人物是目标人物")
         .build());
    systemContentParts.add(ChatCompletionContentPart.builder()
         .type("image_url")
         .imageUrl(new ChatCompletionContentPartImageURL(
            "https://ark-project.tos-cn-beijing.volces.com/doc_image/target.png"))
         .build());
    systemContentParts.add(ChatCompletionContentPart.builder()
         .type("text")
         .text("请确认下面图片中是否含有目标人物")
         .build());

    // 创建system消息
    messagesForReqList.add(ChatMessage.builder()
         .role(ChatMessageRole.SYSTEM)
         .multiContent(systemContentParts)
         .build());

    // 构建user消息内容
    List<ChatCompletionContentPart> userContentParts = new ArrayList<>();
    userContentParts.add(ChatCompletionContentPart.builder()
         .type("text")
         .text("图片1中是否含有目标人物")
         .build());
    userContentParts.add(ChatCompletionContentPart.builder()
         .type("image_url")
         .imageUrl(new ChatCompletionContentPartImageURL(
            "https://ark-project.tos-cn-beijing.volces.com/doc_image/scene_01.png"))
         .build());
    userContentParts.add(ChatCompletionContentPart.builder()
         .type("text")
         .text("图片2中是否含有目标人物")
         .build());
    userContentParts.add(ChatCompletionContentPart.builder()
         .type("image_url")
         .imageUrl(new ChatCompletionContentPartImageURL(
            "https://ark-project.tos-cn-beijing.volces.com/doc_image/scene_02.png"))
         .build());

    // 创建user消息
    messagesForReqList.add(ChatMessage.builder()
         .role(ChatMessageRole.USER)
         .multiContent(userContentParts)
         .build());
    ChatCompletionRequest req = ChatCompletionRequest.builder()
         .model("doubao-seed-1-6-251015") //Replace with Model ID
         .messages(messagesForReqList)
         .maxTokens(300)
         .build();

    service.createChatCompletion(req)
         .getChoices()
         .forEach(choice -> System.out.println(choice.getMessage().getContent()));
    // shutdown service after all requests are finished
    service.shutdownExecutor();
  }
}
\`\`\`

`}></RenderMd></Tabs.TabPane></Tabs>);
 ```

:::tip
图文混排场景，图文顺序可能影响模型输出效果，若结果不符预期，可调整顺序。当多图+一段文字时，建议将文字放在图片之后。
:::
<span id="5fdeb294"></span>
## 视觉定位（Visual Grounding）
请参见教程 [视觉定位 Grounding](/docs/82379/1616136)。
<span id="52afa2e1"></span>
## GUI任务处理
请参见教程 [GUI 任务处理](/docs/82379/1584296)。
<span id="b867b8aa"></span>
# 常见问题

* [使用视觉理解模型时，报错InvalidParameter？](/docs/82379/1359411#effccb14)
