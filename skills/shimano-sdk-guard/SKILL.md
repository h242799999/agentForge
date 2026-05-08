---
name: shimano-sdk-guard
description: Use when writing, reviewing, or generating code that uses shimano-mobile-sdk. Triggers on any mention of ShimanoLoader, BLEDevice, MyBike, Customize, Connection, Auth, WirelessSwitchUnit, or shimano SDK imports. Prevents hallucinated APIs, wrong suspend/non-suspend usage, and incorrect exception handling.
---

# Shimano Mobile SDK Guard

防止在 shimano-mobile-sdk 代码生成中出现幻觉 API、错误的 suspend 用法和错误的异常处理。

## 核心原则

**生成任何 shimano SDK 代码前，必须先核对本文档。** 以下规则基于真实 SDK 源码，任何违背均会导致编译失败或运行时异常。

---

## 1. Suspend vs 非-Suspend（最高风险）

### 非 Suspend 方法（直接调用，不可加 await/withContext）

```kotlin
// Connection
connection.stopScanBLE()
connection.scanBLEDevice(scanFilter, callback)        // 方法本身非suspend，回调异步
connection.scanBLEDeviceInHouse(scanFilter, callback) // 同上

// BLEDevice
bleDevice.registerStatusListener(listener)
bleDevice.findBike()           // 返回缓存的 MyBike，非 suspend
bleDevice.asSensorUnit()       // 非 suspend，但可能抛 UnitException
bleDevice.enableAutoConnect()
bleDevice.disableAutoConnect()

// MyBike
myBike.getWirelessSwitchUnits()  // 返回 Map?，非 suspend

// WirelessSwitchUnit — 关键！
wirelessSwitchUnit.getBatteryLevels()  // ❌ 不是 suspend，不要用 withContext 包裹

// Auth
auth.getUser()   // 非 suspend，返回已登录的 User

// Customize（所有 get*/set* 操作）
customize.getEnabledCategories()
customize.isEnabledCategory(category)
customize.getProfileName(profileType)
customize.setProfileName(profileType, name)
customize.getGearShiftFormType()
customize.getCSTeethPattern()
```

### Suspend 方法（必须在协程中调用）

```kotlin
// ShimanoLoader
suspend fun ShimanoLoader.setup(licenseParams: LicenseParams?, application: Any?)

// BLEDevice
suspend fun connect()
suspend fun disconnect()
suspend fun unlock()
suspend fun getBikeData(): BikeInitialData

// MyBike
suspend fun getCustomize(): Customize
suspend fun scanWirelessSwitchUnits(callback: (WirelessSwitchUnit) -> Unit)
suspend fun pairWirelessSwitchUnit(productSerialNumber: String, pairingIndex: WirelessSwitchPairingIndexType)
suspend fun pairSensorUnits(sensorUnit: SensorUnit)
suspend fun getSensorUnits(): List<SensorUnit>
suspend fun getMyBikeImageUrl(): String?

// Customize
suspend fun updateFromUnit(category: CustomizeCategory?): List<CustomizeCategory>
suspend fun commitSettingValue(category: CustomizeCategory?): List<CustomizeCategory>

// Auth
suspend fun login(params: LoginParams): User
suspend fun logout()
suspend fun checkLogin(): User
suspend fun getContinents(): List<Continent>
suspend fun checkSupportedCountry(countryId: Int): Boolean
suspend fun sendFeedback(feedbackData: FeedbackData)
```

---

## 2. API 真实签名（严禁臆造参数名）

### ShimanoLoader
```kotlin
ShimanoLoader.getConnection(): Connection
ShimanoLoader.getAuth(): Auth
```

### scanBLEDevice（注意：两个方法参数类型完全不同，不可互换）
```kotlin
// 对外 API
fun scanBLEDevice(
    scanFilter: List<ScanFilterType>,       // ScanFilterType，不是 ScanFilterTypeInHouse
    scanResultCallBack: (BLEDevice?, ScanStatus) -> Unit
)

// 内部/室内版本
fun scanBLEDeviceInHouse(
    scanFilter: List<ScanFilterTypeInHouse>, // 注意：不同的枚举类型
    scanResultCallBack: (BLEDevice?, ScanStatus) -> Unit
)
```

### Customize 提交（返回值是**失败**列表，不是成功列表）
```kotlin
// 返回 List<CustomizeCategory> = 失败的项目，空列表 = 全部成功
suspend fun commitSettingValue(category: CustomizeCategory?): List<CustomizeCategory>
suspend fun updateFromUnit(category: CustomizeCategory?): List<CustomizeCategory>

// null 参数 = 操作所有已变更项目
customize.commitSettingValue(null)                              // 全部提交
customize.commitSettingValue(CustomizeCategory.ASSIST_PROFILE)  // 仅提交此类
```

---

## 3. 幻觉 API 黑名单（这些方法不存在）

| 幻觉方法 | 正确替代 |
|---------|---------|
| `customize.setCustomizeMode(...)` | 不存在此方法，直接调用 commit |
| `ScanFilterType.SHIMANO` | 只有 `ScanFilterType.PAIRING` |
| `ScanFilterType.THIRD_PARTY` | 只有 `ScanFilterType.PAIRING` |
| `bleDevice.getStatus()` | `registerStatusListener` 监听状态变化 |
| `myBike.getBikeUnits()` | `myBike.myBikeUnits`（属性，非方法） |
| `connection.getBLEDevices()` | 用 `scanBLEDevice` 回调收集 |

---

## 4. 异常处理规范

### 异常类型与错误码前缀

| 异常类 | 代码前缀 | 关键枚举值 |
|--------|---------|-----------|
| `CommonException` | E-0001 | SDK_NOT_INITIATED, NOT_LOGIN, LICENSE_FAILED |
| `NetworkException` | E-0002 | TOKEN_EXPIRED, NETWORK_TIMEOUT, NETWORK_DISCONNECT |
| `ConnectionException` | E-1001 | BLE_DISABLED, TIME_OUT, AUTHENTICATE_FAILED, NEED_REBONDING |
| `CustomizeException` | E-2001 | COMMIT_FAILED, SYSTEM_LOCKED, NOT_SYNCED, NOT_CONNECTED |
| `MyBikeException` | E-3001 | BLE_DEVICE_NOT_FOUND, WIRELESS_SWITCH_SCAN_FAILED |
| `RidingException` | E-4001 | RIDE_NOT_START, RIDE_STATUS_ERROR |
| `AuthException` | E-5001 | LOGIN_ERROR, ALREADY_LOGGED_IN, NEED_RECONSENT |
| `UnitException` | E-6001/6002 | PAIRING_FAILED, PAIRING_SAME_SIDE_SWITCH |
| `MaintenanceException` | E-7001 | GET_MAINTENANCE_FAILED |

### 正确的异常捕获模式
```kotlin
try {
    val failedCategories = customize.commitSettingValue(CustomizeCategory.ASSIST_PROFILE)
    if (failedCategories.isNotEmpty()) {
        // 部分失败：failedCategories 包含失败的类别
    }
} catch (e: CustomizeException) {
    when (e.errorType) {
        CustomizeException.ErrorEnum.COMMIT_FAILED -> { /* 重连后重试 */ }
        CustomizeException.ErrorEnum.SYSTEM_LOCKED -> { /* 需要解锁 */ }
        CustomizeException.ErrorEnum.NOT_SYNCED -> { /* 先调用 updateFromUnit */ }
        else -> { /* 其他处理 */ }
    }
} catch (e: ConnectionException) {
    // 连接层异常独立处理
}
```

---

## 5. 关键行为约束

### StatusListener 只能注册一个
```kotlin
// 后注册的会覆盖先注册的！
bleDevice.registerStatusListener(listener)  // 唯一活动监听器
```

### getWirelessSwitchUnits() 返回可空 Map
```kotlin
val switchUnits: Map<WirelessSwitchPairingIndexType, WirelessSwitchUnit>? =
    myBike.getWirelessSwitchUnits()
switchUnits?.forEach { (index, unit) -> ... }  // 必须做 null 检查
```

### setup() 必须先于一切调用
```kotlin
// SDK_NOT_INITIATED 错误的根源：调用顺序错误
ShimanoLoader.setup(licenseParams, application)  // 第一步，必须 await
val connection = ShimanoLoader.getConnection()   // 之后才能获取
```

### 扫描回调是同步执行的，禁止长时间操作
```kotlin
// 禁止在回调中做耗时操作
connection.scanBLEDevice(listOf(ScanFilterType.PAIRING)) { device, status ->
    // ❌ 禁止：Thread.sleep(), 网络请求, 复杂计算
    // ✅ 仅做：状态更新、UI 通知、添加到列表
}
```

---

## 6. 标准初始化模板

```kotlin
lifecycleScope.launch {
    try {
        ShimanoLoader.setup(licenseParams, application)
        val connection = ShimanoLoader.getConnection()

        connection.scanBLEDevice(listOf(ScanFilterType.PAIRING)) { device, status ->
            when (status) {
                ScanStatus.SCAN_FOUND_SUCCESS,
                ScanStatus.SCAN_FOUND_MINE_SUCCESS -> {
                    device?.let { foundDevice ->
                        lifecycleScope.launch {
                            foundDevice.connect()
                            val myBike = foundDevice.findBike()  // 非 suspend
                        }
                    }
                }
                ScanStatus.SCAN_TIMEOUT -> connection.stopScanBLE()
                else -> { /* 处理其他状态 */ }
            }
        }
    } catch (e: CommonException) {
        // LICENSE_FAILED / SDK_NOT_INITIATED
    } catch (e: ConnectionException) {
        // BLE_DISABLED 等
    }
}
```
