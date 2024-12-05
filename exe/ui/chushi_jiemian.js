/*
// --------------------------------------初始界面（点击复选框进入）(1)--------------------------------
// 获取三个复选框的元素
const checkBox1 = document.getElementById('cCB1');  // 新建
const checkBox2 = document.getElementById('cCB2');  // 打开
const checkBox3 = document.getElementById('cCB3');  // Option

// 定义复选框切换后的事件监听器
checkBox1.addEventListener('change', () => {
    if (checkBox1.checked) {  // 检查“新建”复选框是否被选中
        window.location.href = 'newPage.html';  // 跳转到“新建”界面
    }
});

checkBox2.addEventListener('change', () => {
    if (checkBox2.checked) {  // 检查“打开”复选框是否被选中
        window.location.href = 'openPage.html';  // 跳转到“打开”界面
    }
});

checkBox3.addEventListener('change', () => {
    if (checkBox3.checked) {  // 检查“Option”复选框是否被选中
        window.location.href = 'optionPage.html';  // 跳转到“Option”界面
    }
});
*/

// --------------------------------------初始界面（点击复选框进入）(2)--------------------------------
// 获取三个复选框的元素
const checkBox1 = document.getElementById('cCB1');  // 新建
/*const checkBox2 = document.getElementById('cCB2');  // 打开
const checkBox3 = document.getElementById('cCB3');  // Option*/

// 定义复选框切换后的事件监听器
checkBox1.addEventListener('change', () => {
    if (checkBox1.checked) {  // 检查“新建”复选框是否被选中
        window.location.href = 'start.html';  // 跳转到“新建”界面
        setTimeout(() => { checkBox1.checked = false; }, 300);  // 恢复复选框状态
    }
});

/*checkBox2.addEventListener('change', () => {
    if (checkBox2.checked) {  // 检查“打开”复选框是否被选中
        window.location.href = 'openPage.html';  // 跳转到“打开”界面
        setTimeout(() => { checkBox2.checked = false; }, 300);  // 恢复复选框状态
    }
});

checkBox3.addEventListener('change', () => {
    if (checkBox3.checked) {  // 检查“Option”复选框是否被选中
        window.location.href = 'optionPage.html';  // 跳转到“Option”界面
        setTimeout(() => { checkBox3.checked = false; }, 300);  // 恢复复选框状态
    }
});*/
