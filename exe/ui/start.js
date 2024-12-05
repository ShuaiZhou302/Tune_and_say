// --------------------------------------旋钮--------------------------------
// 通用函数，为每个旋钮绑定旋转和滚轮控制逻辑
function setupKnob(knobId, angleDisplayId) {
    const knob = document.querySelector(`#${knobId}`); // 获取旋钮元素
    const knobAngleDisplay = document.querySelector(`#${angleDisplayId}`); // 获取角度显示元素
    let isDragging = false;
    let currentAngle = 0;
    let previousAngle = 0;

    // 获取角度函数
    function getAngle(event) {
        const rect = knob.getBoundingClientRect();
        const centerX = rect.left + rect.width / 2;
        const centerY = rect.top + rect.height / 2;
        const x = event.clientX - centerX;
        const y = event.clientY - centerY;
        return Math.atan2(y, x) * (180 / Math.PI);
    }

    // 处理角度连续性问题
    function normalizeAngle(angle) {
        if (angle > 180) return angle - 360;
        if (angle < -180) return angle + 360;
        return angle;
    }

    // 鼠标按下时
    knob.addEventListener('mousedown', (event) => {
        isDragging = true;
        previousAngle = getAngle(event);
        document.body.style.cursor = 'grabbing';
    });

    // 鼠标移动时
    document.addEventListener('mousemove', (event) => {
        if (isDragging) {
            let angle = getAngle(event);
            let deltaAngle = normalizeAngle(angle - previousAngle);
            currentAngle += deltaAngle;
            if (knobId === 'knob2') {
                setHost("audio.soundDirection", currentAngle);
            }
            knob.style.transform = `rotate(${currentAngle}deg)`;
            knobAngleDisplay.textContent = `Angle: ${Math.round(currentAngle)}°`;
            previousAngle = angle;
        }
    });

    // 鼠标释放时
    document.addEventListener('mouseup', () => {
        isDragging = false;
        document.body.style.cursor = 'default';
    });

    // 滚轮滚动时
    knob.addEventListener('wheel', (event) => {
        const delta = event.deltaY > 0 ? 5 : -5; // 向下滚动增加角度，向上滚动减少角度
        currentAngle += delta;
        if (knobId === 'knob2') {
            setHost("audio.soundDirection", currentAngle);
        }
        knob.style.transform = `rotate(${currentAngle}deg)`;
        knobAngleDisplay.textContent = `Angle: ${Math.round(currentAngle)}°`;
        event.preventDefault(); // 防止页面滚动
    });
}

// 初始化两个旋钮
setupKnob('knob1', 'knob1-angle');
setupKnob('knob2', 'knob2-angle');

// 获取播放暂停按钮和复选框
const playPauseToggle = document.getElementById('playPauseToggle');
const startPauseBtn = document.getElementById('startPauseBtn');
const slider = document.querySelector('.level');
const volumeLevel = document.querySelector('.volume-level');

// --------------------------------------音量可视化--------------------------------
const volumeCanvas = document.getElementById('volumeCanvas'); // 获取页面中的画布元素
const ctx = volumeCanvas.getContext('2d'); // 获取画布的 2d 上下文，用于绘图

function drawVolumeVisualization() {
    if (!window.audioPlaying) return;
    requestAnimationFrame(drawVolumeVisualization); // 请求下一帧动画，保持循环绘制
    const rawData = window.audioFftData ?? [];
    if (rawData.length === 0) return;
    const fftData = [];
    for (let i = 0; i < rawData.length / 2; i++) {
        fftData.push((Math.abs(rawData[i * 2]) + Math.abs(rawData[i * 2 + 1])) / 2);
    }
    const bufferLength = rawData.length / 2; // 获取频率数据的数量

    ctx.fillStyle = '#f0f0f0'; // 设置背景颜色为浅灰色
    ctx.fillRect(0, 0, volumeCanvas.width, volumeCanvas.height); // 清空画布，绘制背景色

    const barWidth = (volumeCanvas.width / bufferLength) * 2.5; // 设置每个条形图的宽度
    let x = 0; // 初始化 x 坐标，用于绘制每个条形图的位置

    for (let i = 0; i < bufferLength; i++) { // 循环遍历每个频率数据
        const barHeight = fftData[i] * volumeCanvas.height * 1.414; // 获取当前频率数据的强度值
        ctx.fillStyle = 'rgba(76, 175, 80, 0.7)'; // 设置条形图的颜色为半透明绿色
        ctx.fillRect(x, volumeCanvas.height - barHeight / 2, barWidth, barHeight / 2); // 绘制条形图
        x += barWidth + 1; // 更新 x 坐标，为下一个条形图留出空间
    }
}

// --------------------------------------音量显示--------------------------------
slider.addEventListener('input', async function () {
    const gainValue = slider.value / 100;  // 将滑块值从 0-100 转换为 0-1 的增益值
    setHost("audio.volume", gainValue).catch(e => console.error(e))
    console.log(await getHost("audio.volume"))
    volumeLevel.textContent = `${slider.value}%`;  // 更新音量百分比显示
    updateVolumeDisplay(slider.value);  // 更新电平显示（新加入的）
});

const volumeCanvasElement = document.getElementById("dynamicVolumeCanvas"); // 获取画布元素
const volumeContext = volumeCanvasElement.getContext("2d"); // 获取画布的上下文

// 更新音量显示的函数
function updateVolumeDisplay(level) {
    if (!window.audioPlaying) {
        volumeContext.clearRect(0, 0, volumeCanvasElement.width, volumeCanvasElement.height);
        return;
    }
    const maxBars = 13;  // 最大显示矩形数
    const barHeight = 20; // 每个矩形的高度
    const barWidth = 80;  // 每个矩形的宽度

    // 根据电平计算显示的矩形数量
    const numberOfBars = Math.min(Math.floor(level / 0.008), maxBars);  // 这里的0.008可以修改，调整电平与矩形数量的对应关系

    // 清空画布，准备重绘
    volumeContext.clearRect(0, 0, volumeCanvasElement.width, volumeCanvasElement.height);

    for (let i = 0; i < numberOfBars; i++) {
        // 计算颜色渐变
        const green = Math.max(255 - i * 20, 0);  // 随着矩形增加，绿色逐渐减少
        const red = Math.min(i * 20, 255);        // 随着矩形增加，红色逐渐增加
        const color = `rgb(${red}, ${green}, 0)`; // 形成从绿到红的颜色渐变

        volumeContext.fillStyle = color;  // 设置填充颜色
        volumeContext.fillRect(
            (volumeCanvasElement.width - barWidth) / 2,  // 使矩形居中
            volumeCanvasElement.height - (i + 1) * barHeight,  // 计算矩形的位置
            barWidth,  // 矩形的宽度
            barHeight  // 矩形的高度
        );
    }
}

window.audioPlaying = false;

// 播放/暂停按钮控制麦克风的开关
playPauseToggle.addEventListener('change', function () {
    if (this.checked) {
        window.audioPlaying = true;
        drawSpectrogramGraph();
        drawVolumeVisualization();
    } else {
        window.audioPlaying = false;
    }
});

// 订阅音频电平更新，并根据滑块的增益调整电平显示
subscribeHost("audio.rmsLevel", "levelDisplayJS", audio_level => {
    // 获取当前电平并显示，使用滑块设置的音量进行调整
    const adjustedLevel = audio_level * (slider.value / 100);  // 将电平调整为滑块设置的音量
    document.getElementById("current-level").innerText = adjustedLevel.toFixed(16);  // 显示当前调整后的电平
    updateVolumeDisplay(adjustedLevel); // 根据调整后的电平更新音量显示
});

// 订阅音频输入设备更新事件
subscribeHost("audio.inputList", "audioInputUpdateJS", ports => {
    const select = document.getElementById("audioInputListSelect");
    select.innerHTML = "";
    const portSet = new Set();
    for (const port of ports) {
        portSet.add(port);
    }
    for (const port of portSet) {
        const option = document.createElement("option");
        option.value = port;
        option.text = port;
        select.appendChild(option);
    }
});

subscribeHost("audio.fftData", "audioSpectreUpdateJS", fftData => {
    window.audioFftData = fftData;
})

// --------------------------------------频谱图绘制--------------------------------
const spectrogramCanvas = document.getElementById('spectrogramCanvas');
const spectrogramCtx = spectrogramCanvas.getContext('2d');

// 获取频率数据
function drawSpectrogramGraph() {
    if (!window.audioPlaying) return;
    requestAnimationFrame(drawSpectrogramGraph);  // 请求下一帧动画

    const fftData = window.audioFftData ?? [];
    const bufferLength = fftData.length; // 获取频率数据的数量

    const canvasWidth = spectrogramCanvas.width;
    const canvasHeight = spectrogramCanvas.height;

    // copy 0~canvasWidth-2 to 1~canvasWidth-1 on canvas
    const imageData = spectrogramCtx.getImageData(0, 0, canvasWidth - 1, canvasHeight);
    spectrogramCtx.putImageData(imageData, 1, 0);

    // 绘制第一列的颜色
    const columnImageData = spectrogramCtx.createImageData(1, canvasHeight);
    for (let i = 0; i < canvasHeight; i++) {
        const floatIndex = (i / canvasHeight) * bufferLength;
        const r = Math.abs(sampleFrom(fftData, floatIndex));
        columnImageData.data[i * 4] = Math.min(255, Math.floor(255 * (-Math.pow(Math.E, -r * 1.7) + 1.1843)));
        columnImageData.data[i * 4 + 1] = 79;
        columnImageData.data[i * 4 + 2] = 79;
        columnImageData.data[i * 4 + 3] = 255;
    }
    spectrogramCtx.putImageData(columnImageData, 0, 0);
}

window.addEventListener("load", () => {
    drawSpectrogramGraph();
    drawVolumeVisualization();
});

/**
 * 根据浮点索引获取数组中的元素并线性插值
 * @param array {Array<number>}
 * @param floatIndex {number}
 */
function sampleFrom(array, floatIndex) {
    const integerIndex = Math.floor(floatIndex);
    const nextIndex = Math.ceil(floatIndex);
    const fraction = floatIndex - integerIndex;
    return array[integerIndex] * (1 - fraction) + array[nextIndex] * fraction;
}