import os
from torchvision.datasets.vision import VisionDataset
from PIL import Image


class CustomDataset(VisionDataset):
    def __init__(self, root, transform=None, target_transform=None):
        super(CustomDataset, self).__init__(root, transform=transform, target_transform=target_transform)
        self.data = []
        self.targets = []
        self.classes = []

        # Suponha que as imagens estão organizadas por pastas, onde cada pasta é uma classe
        for class_name in os.listdir(root):
            class_path = os.path.join(root, class_name)
            if os.path.isdir(class_path):
                self.classes.append(class_name)
                for img_name in os.listdir(class_path):
                    img_path = os.path.join(class_path, img_name)
                    self.data.append(img_path)
                    self.targets.append(class_name)

        # Criar um mapeamento de classe para índice
        self.class_to_idx = {cls_name: idx for idx, cls_name in enumerate(self.classes)}
        self.targets = [self.class_to_idx[target] for target in self.targets]

    def __len__(self):
        return len(self.data)

    def __getitem__(self, index):
        img_path = self.data[index]
        label = self.targets[index]

        # Carregar a imagem
        img = Image.open(img_path).convert("RGB")

        # Aplicar transformações (se definidas)
        if self.transform:
            img = self.transform(img)
        if self.target_transform:
            label = self.target_transform(label)

        return img, label


# Exemplo de uso
if __name__ == "__main__":
    from torchvision import transforms
    from torch.utils.data import DataLoader

    # Diretório contendo as pastas de classes
    dataset_root = "/caminho/para/seu/dataset"

    # Transformações para as imagens
    transform = transforms.Compose([
        transforms.Resize((128, 128)),
        transforms.ToTensor(),
    ])

    # Criar o dataset
    dataset = CustomDataset(root=dataset_root, transform=transform)

    # Criar um DataLoader
    dataloader = DataLoader(dataset, batch_size=16, shuffle=True)

    # Iterar pelo DataLoader
    for images, labels in dataloader:
        print(f"Batch de imagens: {images.shape}, Labels: {labels}")
