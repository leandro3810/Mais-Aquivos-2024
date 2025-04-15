import re

class Tokenizer:
    def __init__(self, mode="word"):
        """
        Inicializa o tokenizador com o modo especificado.
        Modes disponíveis:
        - "word": Tokeniza o texto em palavras (padrão).
        - "sentence": Tokeniza o texto em frases.
        """
        self.mode = mode
        
    def tokenize(self, text):
        """
        Tokeniza o texto com base no modo especificado.
        
        Args:
            text (str): O texto a ser tokenizado.
        
        Returns:
            list: Uma lista de tokens (palavras ou frases).
        """
        if self.mode == "word":
            # Divide o texto em palavras, ignorando pontuações.
            return re.findall(r'\b\w+\b', text)
        elif self.mode == "sentence":
            # Divide o texto em frases.
            return re.split(r'(?<=[.!?]) +', text)
        else:
            raise ValueError("Modo inválido. Escolha 'word' ou 'sentence'.")

# Exemplo de uso
if __name__ == "__main__":
    text = "Olá, mundo! Este é um exemplo de tokenizador. Ele funciona muito bem."
    
    # Tokenizador de palavras
    word_tokenizer = Tokenizer(mode="word")
    print("Tokens por palavra:", word_tokenizer.tokenize(text))
    
    # Tokenizador de frases
    sentence_tokenizer = Tokenizer(mode="sentence")
    print("Tokens por frase:", sentence_tokenizer.tokenize(text))
