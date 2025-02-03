import ollama

def request(question, image=''):
    res = ollama.chat(
    #model='dolphin-llama3:8b',
    model='llama3.2-vision:11b',
    messages=[{
        'role': 'user',
        'content': question,
    }])
    return res['message']['content']


def template(desc):
    text = f"""
    Você é um analista de especialista de dados de finanças pessoais e está trabalhando em um projeto para realização de limpeza de dados, seu objetivo principal do trabalho é escolher uma categoria adequada para cada lançamento financeiro que estarei enviando abaixo.
    
    Veja que cada categoria terá suas regras:
    - Receita: Só será uma receita se houver a frase "Transferência Recebida"
    - Fatura: Só será fatura se houve a frase "Pagamento de Fatura".
    - Investimento: Aplicação RDB,
    - Resgate: Regate RDB
    - Compras Online:
    - Acessórios:
    - Educação: 

    Veja que cada categoria terá seus usuários chaves portanto além das informações acima se conter algum nome dos listados deve ser vinculado a determinada categoria.
    - Alimentação: AISLAN CORDEIRO DO AMARAL, EDILSON SEBASTIAO DA SILVA, IVANILDA RODRIGUES DE MEDEIROS ARAUJO, CARVALHO E SUASSUNA LTDA
    - Acessórios: JOBSON SOARES
    - Transação Interna: THIAGO BENEVIDE DE MORAES
    - Cabeleireiro: DANILO GONCALVES PEREIRA
    - Acessórios: WORLD PLAYER
    - Compras Online: AMAZON, UDEMY, NETSHOES, d.LOCAL, PAYPAL, MERCADO LIVRE
    - Striming: HBO, SPORTFY, 
    - Pagamento para Terceiro: Se não tiver os nomes acima deve ser considerado como pagamento para terceiro.

    Escolha os dados de acordo com as seguinte categorias:
    - Alimentação
    - Saúde
    - Receita
    - Educação
    - Transporte
    - Cabeleireiro
    - Entreterimento
    - Telefone
    - Pagamento para Terceiro
    - Fatura
    - Acessórios
    - Transação Interna
    - Investimento
    - Compras Online
    - Striming
    - Resgate



    Escolha a categoria deste item:
    {desc}
    Responda apenas com a categoria sem nenhum caracterie especial ou pontuação apenas a categoria.
    """
    return text


