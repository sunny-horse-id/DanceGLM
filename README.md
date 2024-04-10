![Demo webpage](assets/img.png)
![Demo webpage](assets/img_1.png)
![Demo webpage](assets/dance.png)
## 安装

我们建议通过 [Conda](https://docs.conda.io/en/latest/) 进行环境管理。

执行以下命令新建一个 conda 环境并安装所需依赖：

```bash
conda create -n sway python=3.10
activate sway
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install git+https://github.com/facebookresearch/pytorch3d.git
pip install git+https://github.com/rodrigo-castellon/jukemirlib.git
pip install accelerate
#此处根据您的服务器配置自行选择
accelerate config
pip install -r requirements.txt
```
