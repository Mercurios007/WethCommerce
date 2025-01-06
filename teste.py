def calcular_comissao(preco_produto, comissao_percentual=10):
    # Calcula o valor da comissão
    comissao = (preco_produto * comissao_percentual) / 100
    # Subtrai a comissão do preço original do produto
    preco_com_comissao = preco_produto - comissao
    return comissao, preco_com_comissao

# Exemplo de uso
preco_produto = float(input("Digite o preço do produto: R$ "))
comissao, preco_com_comissao = calcular_comissao(preco_produto)

print(f"A comissão de 10% sobre o produto é: R$ {comissao:.2f}")
print(f"O preço do produto após a comissão é: R$ {preco_com_comissao:.2f}")
