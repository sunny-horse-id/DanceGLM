<template>
  <el-tabs v-model="activeName" class="demo-tabs">
    <el-tab-pane v-for="(item, index) in address" :key="index" :label="`Module ${index}`" :name="`module_${index}`">
      <!--  模型的播放与暂停  -->
      <div class="button-wrapper">
        <button @click="toggleAnimation">{{ isPlaying ? '暂停动画' : '播放动画' }}</button>
      </div>
    </el-tab-pane>
  </el-tabs>
</template>

<script setup>
/* 导入相关依赖 */
// Vue驱动相关导入
import { ref, watch } from 'vue'
// API借口的导入
import { getAddressAPI } from "@/apis/play.js";
// Tree.js的导入
import * as THREE from "three";
import {OrbitControls} from "three/addons/controls/OrbitControls.js";
import {FBXLoader} from "three/addons/loaders/FBXLoader.js";


/* 定义相关变量 */
const activeName = ref('module_0')  // 页面变量
const address = ref([]) // fbx和wav地址
const isPlaying = ref(false)  // 播放控制变量
const selectedFile = ref(0) // 页面号
let scene, renderer, camera, mixer, clock, backgroundMusic; // fbx播放相关变量


/* 函数定义 */
// 获取地址的初始化函数
const getAddress = async () => {
  address.value = (await getAddressAPI()).data
}
getAddress()  // 获取地址初始化

// fbx加载
function setupAnimation(fbxPath, wavPath) {
  clock = new THREE.Clock();

  window.addEventListener('resize', function () {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  });

  function initRenderer() {
    renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.setSize(window.innerWidth, window.innerHeight);
    document.body.appendChild(renderer.domElement);
  }

  function initControls() {
    // eslint-disable-next-line no-unused-vars
    const controls = new OrbitControls(camera, renderer.domElement);
  }

  function initScene() {
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0xa0a0a0);
  }

  function initAxesHelper() {
    const axesHelper = new THREE.AxesHelper(1);
    scene.add(axesHelper);
  }

  function initLight() {
    const hemiLight = new THREE.HemisphereLight(0xffffff, 0x444444);
    scene.add(hemiLight);
  }

  function initMeshes() {
    const loader = new FBXLoader();
    loader.load(fbxPath, function (fbx) {
      fbx.scale.set(0.1, 0.1, 0.1);
      fbx.position.set(30, -15, 5);
      scene.add(fbx);
      mixer = new THREE.AnimationMixer(fbx);
      const action = mixer.clipAction(fbx.animations[0]);
      action.play();
    });
  }

  function initCamera() {
    camera = new THREE.PerspectiveCamera(
        45, window.innerWidth / window.innerHeight, 1, 1000);
    camera.position.set(10, 20, 30);
  }

  function initBackgroundMusic() {
    backgroundMusic = new Audio(wavPath);
    backgroundMusic.loop = true;
    backgroundMusic.volume = 0.5; // Adjust volume as needed
  }

  function animate() {
    let delta = clock.getDelta();
    requestAnimationFrame(animate);
    if (mixer && isPlaying.value) {
      mixer.update(delta);
      if (backgroundMusic.paused) {
        backgroundMusic.play();
      }
    } else {
      backgroundMusic.pause();
    }
    renderer.render(scene, camera);
  }

  initRenderer();
  initScene();
  initAxesHelper();
  initCamera();
  initLight();
  initMeshes();
  initControls();
  initBackgroundMusic();
  animate();
}

// Tree.js场景清空辅助函数
function resizeHandler() {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
}

// Three.js场景清空主函数
function clearAnimation() {
  // 清除场景中的所有对象
  scene.remove(...scene.children);

  // 重置渲染器大小
  renderer.setSize(1, 1); // 将渲染器大小设置为1x1像素

  // 清除事件监听器
  window.removeEventListener('resize', resizeHandler);

  // 清除动画混合器
  if (mixer) {
    mixer.stopAllAction();
    mixer = null;
  }

  // 清除背景音乐
  if (backgroundMusic) {
    backgroundMusic.pause();
    backgroundMusic = null;
  }
}

//播放与暂停控制函数
function toggleAnimation() {
  isPlaying.value = !isPlaying.value;
}

/* 变量改变监听函数 */
// 监听标签页名的变化
watch(activeName, (newValue) => {
  selectedFile.value = newValue.split('_')[1]
})

// 监听页号的变化，用于清空场景并重新加载模型
watch(selectedFile, (newValue) => {
  clearAnimation()
  setupAnimation(address.value[newValue][0], address.value[newValue][1])
  isPlaying.value = false
});

// 监听地址的变化，用于加载模型
watch(address, (newValue) => {
  setupAnimation(newValue[0][0], newValue[0][1]);
});
</script>

<style>

</style>