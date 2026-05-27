# Modbus Gateway - HACS Custom Component

一个强大的 Home Assistant 自定义组件，用于集成 Modbus TCP/RTU/ASCII 协议设备。支持标准 Modbus 协议设备，也支持非标准协议的 Modbus 设备集成。

## 📦 安装

### 通过 HACS 安装（推荐）

1. 确保已安装 [HACS](https://hacs.xyz/)
2. 在 HACS → 自定义仓库中添加此仓库 URL，类别选择 "Integration"
3. 点击 "下载"
4. 重启 Home Assistant

### 手动安装

1. 将 `custom_components/modbus_gateway/` 文件夹复制到 Home Assistant 的 `config/custom_components/` 目录
2. 重启 Home Assistant

## 🚀 快速开始

1. 进入 **设置 → 设备与服务 → 添加集成**
2. 搜索 **Modbus Gateway**
3. 选择连接类型（TCP / RTU / ASCII）
4. 填入连接参数
5. 添加数据点（传感器、开关、灯、空调等）

## ✨ 功能特性

### 1. 灵活连接配置
- **Modbus TCP**：IP 地址 + 端口
- **Modbus RTU/ASCII (RS-485)**：串口路径、波特率、校验方式、数据位、停止位
- 可配置超时、重试次数、请求间隔等

### 2. 丰富的实体支持
通过 UI 便捷添加数据点，选择实体类型后 HA 自动生成对应组件：

| 实体类型 | 描述 | 支持操作 |
|---------|------|---------|
| 🅰️ **sensor** | 传感器 (只读) | 读取寄存器值 |
| 🔲 **binary_sensor** | 二进制传感器 (0/1) | 读取线圈/离散量 |
| 🔘 **switch** | 开关 | 读取 + 开关控制 |
| 💡 **light** | 灯光 | 亮度控制、开关 |
| 🌡️ **climate** | 空调/温控 | 温度设置、模式切换 |
| 🪟 **cover** | 窗帘/卷帘/遮阳 | 开/关/位置控制 |
| 🔢 **number** | 数值输入 | 滑块/数值输入 |
| 🔴 **button** | 自定义按钮 | 执行原始 Modbus 指令 |
| 📋 **select** | 下拉选择 | 多选项选择 |

### 3. 数据类型全覆盖
支持多种 Modbus 数据类型解码/编码：
- **uint16 / int16** - 16 位无符号/有符号整数
- **uint32 / int32** - 32 位无符号/有符号整数
- **float32** - 32 位 IEEE 754 浮点数
- **uint64 / int64** - 64 位整数
- **string** - 字符串（每个寄存器 2 个 ASCII 字符）
- **custom** - 自定义 Python struct 格式

### 4. 非标准协议支持（Button 按钮模式）
类似红外遥控器，通过按钮预设原始 Modbus 报文，点击即可发送：

**适用场景：** 私有协议、自定义功能码、需要发送原始报文的设备

**支持的负载格式：**
- `HEX` - 十六进制字节码：`010600010001`
- `RAW` - 原始字节字符串
- `DEC` - 十进制值自动编码

### 5. 多从站支持
每个数据点可单独指定从站 ID (slave)，一个连接下管理多个设备。

### 6. 缩放与偏移
对原始寄存器值进行缩放和偏移计算：`最终值 = 原始值 × 缩放系数 + 偏移量`

## ⚙️ 配置示例

### TCP 连接
```
名称: 太阳能逆变器
IP: 192.168.1.100
端口: 502
从站 ID: 1
```

### 串口连接
```
名称: PLC 控制器
串口: /dev/ttyUSB0
波特率: 9600
校验: N (无校验)
停止位: 1
数据位: 8
```

### 数据点示例
| 名称 | 地址 | 类型 | 数据类型 | 实体类型 | 读写 |
|------|------|------|---------|---------|------|
| 温度 | 100 | Holding | uint16 | sensor | 只读 |
| 开关控制 | 0 | Coil | - | switch | 读写 |
| 亮度调节 | 200 | Holding | uint16 | light | 读写 |
| 目标温度 | 300 | Holding | float32 | climate | 读写 |

## 🔧 非标准协议 - Button 使用示例

对于非标准 Modbus 协议设备，使用 **button** 类型添加：

1. 添加数据点，实体类型选择 **button**
2. 填入自定义名称（如"开机"、"关机"、"模式切换"）
3. 输入十六进制报文（如 `010600010001` 表示写入单寄存器）
4. 点击按钮即可发送

**报文格式说明（HEX）：**
- `010600010001` = 从站ID(01) + 功能码(06写单寄存器) + 地址(0001) + 数据(0001)
- `010500010000` = 从站ID(01) + 功能码(05写单线圈) + 地址(0001) + 数据(0000=关/FF00=开)

## 🏗️ 项目结构

```
modbus_gateway/
├── custom_components/
│   └── modbus_gateway/
│       ├── __init__.py         # 组件入口与生命周期管理
│       ├── config_flow.py      # UI 配置流程
│       ├── const.py            # 常量和配置键
│       ├── entity.py           # 基础实体类
│       ├── modbus_hub.py       # Modbus 连接管理与数据读写
│       ├── sensor.py           # 传感器平台
│       ├── binary_sensor.py    # 二进制传感器平台
│       ├── switch.py           # 开关平台
│       ├── light.py            # 灯光平台
│       ├── climate.py          # 空调/温控平台
│       ├── cover.py            # 窗帘/卷帘平台
│       ├── number.py           # 数值输入平台
│       ├── button.py           # 自定义按钮平台 (非标准协议)
│       ├── select.py           # 下拉选择平台
│       ├── manifest.json       # 组件清单
│       └── translations/       # 多语言翻译
│           ├── zh-Hans.json    # 简体中文
│           └── en.json         # English
├── hacs.json                   # HACS 配置
├── README.md                   # 本文档
├── LICENSE                     # 许可证
└── info.md                     # HACS 展示信息
```

## 📋 前提条件

- Home Assistant 2024.6.0 或更高版本
- 需要接入的 Modbus 设备（TCP / RS-485 串口）

## 🔒 数据安全

- 配置文件存储在 Home Assistant 的配置条目中
- 连接参数仅在本地使用，不会上传到任何外部服务

## 🐛 问题反馈

如有问题或功能建议，请在 GitHub Issues 中提交。

## 📄 许可证

MIT License
