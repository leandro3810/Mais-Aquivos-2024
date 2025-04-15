import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, transforms

# Definir a rede neural
class SimpleNN(nn.Module):
    def __init__(self):
        super(SimpleNN, self).__init__()
        self.fc1 = nn.Linear(28 * 28, 128)  # Camada densa 1
        self.relu = nn.ReLU()              # Função de ativação
        self.fc2 = nn.Linear(128, 10)      # Camada densa 2 (saída)

    def forward(self, x):
        x = x.view(-1, 28 * 28)  # Flatten da imagem
        x = self.fc1(x)
        x = self.relu(x)
        x = self.fc2(x)
        return x

# Hiperparâmetros
batch_size = 64
epochs = 5
learning_rate = 0.001

# Pré-processamento dos dados
transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize((0.5,), (0.5,))
])

# Dataset e DataLoader
train_dataset = datasets.MNIST(root='./data', train=True, download=True, transform=transform)
train_loader = torch.utils.data.DataLoader(dataset=train_dataset, batch_size=batch_size, shuffle=True)

test_dataset = datasets.MNIST(root='./data', train=False, download=True, transform=transform)
test_loader = torch.utils.data.DataLoader(dataset=test_dataset, batch_size=batch_size, shuffle=False)

# Inicializar modelo, função de perda e otimizador
model = SimpleNN()
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=learning_rate)

# Treinamento
for epoch in range(epochs):
    model.train()
    for batch_idx, (data, target) in enumerate(train_loader):
        # Zerar gradientes
        optimizer.zero_grad()
        # Forward pass
        output = model(data)
        # Calcular perda
        loss = criterion(output, target)
        # Backward pass e atualização dos pesos
        loss.backward()
        optimizer.step()

        if batch_idx % 100 == 0:
            print(f'Epoch [{epoch+1}/{epochs}], Step [{batch_idx}/{len(train_loader)}], Loss: {loss.item():.4f}')

# Avaliação no conjunto de teste
model.eval()
correct = 0
total = 0
with torch.no_grad():
    for data, target in test_loader:
        output = model(data)
        _, predicted = torch.max(output.data, 1)
        total += target.size(0)
        correct += (predicted == target).sum().item()

print(f'Accuracy on test set: {100 * correct / total:.2f}%')
