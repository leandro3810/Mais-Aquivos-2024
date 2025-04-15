from transformers import AutoTokenizer, AutoModelForSequenceClassification

def load_transformer_model(model_name="bert-base-uncased", num_labels=2):
    """
    Carrega um modelo Transformer pré-treinado com um tokenizador.

    Args:
        model_name (str): O nome do modelo pré-treinado no Hugging Face Hub.
        num_labels (int): O número de classes para classificação.

    Returns:
        model: Modelo Transformer pré-treinado.
        tokenizer: Tokenizador associado ao modelo.
    """
    # Carregando o tokenizador
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    # Carregando o modelo pré-treinado para classificação
    model = AutoModelForSequenceClassification.from_pretrained(
        model_name, 
        num_labels=num_labels
    )

    print(f"Modelo {model_name} carregado com sucesso!")
    return model, tokenizer


if __name__ == "__main__":
    # Exemplo de uso
    model_name = "bert-base-uncased"
    num_labels = 2  # Exemplo: Classificação binária

    model, tokenizer = load_transformer_model(model_name, num_labels)

    # Testando o tokenizador
    example_text = "Este é um exemplo de texto para o modelo Transformer."
    inputs = tokenizer(example_text, return_tensors="pt")

    # Fazendo uma previsão
    outputs = model(**inputs)
    print("Saída do modelo:", outputs)
