# Modbus Gateway

[![HACS Default](https://img.shields.io/badge/HACS-Default-orange.svg)](https://hacs.xyz)
[![GitHub Release](https://img.shields.io/github/v/release/gelin006/modbus_gateway)](https://github.com/gelin006/modbus_gateway/releases)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2024.6+-blue.svg)](https://www.home-assistant.io/)

一个功能强大的 Home Assistant Modbus 集成组件，通过 HACS 安装管理。

- **标准协议**：支持 Modbus TCP/RTU/ASCII，灵活的连接配置
- **丰富实体**：传感器、开关、灯、空调、窗帘、按钮、选择器等
- **非标准协议**：自定义按钮模式，像红外遥控器一样自由定义
- **UI 配置**：无需 YAML，全部通过 Home Assistant 界面完成

## 安装

通过 HACS 添加此仓库，类别选择 **Integration**。

## 使用

设置 → 设备与服务 → 添加集成 → 搜索 "Modbus Gateway"

## 功能

- 支持 Modbus TCP 和 RTU/ASCII 串口连接
- 可配置波特率、校验方式、停止位等串口参数
- 支持 9 种实体类型：sensor, binary_sensor, switch, light, climate, cover, number, button, select
- 支持 uint16/32/64、int16/32/64、float32、string、custom struct 数据类型
- 缩放/偏移/精度配置
- 非标准协议原始报文按钮
- 多从站支持
- HA 设备注册表集成
