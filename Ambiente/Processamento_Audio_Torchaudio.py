import torchaudio
import torchaudio.transforms as T
import matplotlib.pyplot as plt

# Função para visualizar waveform
def plot_waveform(waveform, sample_rate, title="Waveform", xlim=None):
    plt.figure(figsize=(12, 4))
    plt.plot(waveform.t().numpy())
    if xlim:
        plt.xlim(xlim)
    plt.title(title)
    plt.xlabel("Time (frames)")
    plt.ylabel("Amplitude")
    plt.grid()
    plt.show()

# Carregar arquivo de áudio
def load_audio(filepath):
    waveform, sample_rate = torchaudio.load(filepath)
    print(f"Shape do Waveform: {waveform.size()}")
    print(f"Taxa de Amostragem: {sample_rate} Hz")
    return waveform, sample_rate

# Aplicar transformações no áudio
def apply_transforms(waveform, sample_rate):
    # Resample para 16 kHz
    resample_transform = T.Resample(orig_freq=sample_rate, new_freq=16000)
    waveform_resampled = resample_transform(waveform)
    
    # Normalizar
    normalize_transform = T.Vol(0.5)
    waveform_normalized = normalize_transform(waveform_resampled)
    
    # Adicionar ruído
    noise = torch.randn_like(waveform_normalized) * 0.01
    waveform_noisy = waveform_normalized + noise
    
    return waveform_resampled, waveform_noisy

# Caminho para o arquivo de áudio
audio_filepath = "seu_audio.wav"  # Substitua pelo caminho do arquivo desejado

# 1. Carregar áudio
waveform, sample_rate = load_audio(audio_filepath)

# 2. Visualizar waveform original
plot_waveform(waveform, sample_rate, title="Waveform Original")

# 3. Aplicar transformações
waveform_resampled, waveform_noisy = apply_transforms(waveform, sample_rate)

# 4. Visualizar waveform transformado
plot_waveform(waveform_resampled, 16000, title="Waveform Resampled (16 kHz)")
plot_waveform(waveform_noisy, 16000, title="Waveform with Noise")
