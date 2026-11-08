# Simulador do canhao de Newton

Uma demonstracao visual de como a velocidade horizontal de um projetil e a gravidade podem produzir uma orbita ao redor da Terra.

## Executar

```bash
python -m pip install -r requirements.txt
python main.py
```

## Usar

- Edite a aceleracao do canhao em `m/s2` e a duracao do disparo em segundos. Clique no campo e digite um numero; use `,` ou `.` como separador decimal e pressione Enter.
- Pressione **Disparar** ou **Espaco** para comecar. A velocidade inicial resulta de `aceleracao x duracao`; o canhao ideal acelera a bola durante o disparo e, apos a saida, a gravidade atua sobre ela.
- **Reiniciar** ou **R** limpa a simulacao. **P** pausa ou continua.
- Use **+** e **-** para alterar a velocidade da simulacao sem mudar as unidades fisicas.

Os valores iniciais sao `10.000 m/s2` por `0,77299 s`, que fornecem aproximadamente `7.730 m/s` de velocidade horizontal, proximo da velocidade orbital circular na altitude padrao do canhao (`300 km`). A velocidade orbital nessa altitude e cerca de `7.730 m/s`; a velocidade de escape e cerca de `10.932 m/s`.

Para mudar a distancia entre o canhao e a Terra, edite `CANNON_ALTITUDE_M` no inicio de `main.py` (valor em metros; o padrao e `300_000.0`, ou `300 km`). A posicao inicial da bola, o desenho do canhao e as velocidades orbital/de escape de referencia acompanham essa variavel.

O modelo idealiza o canhao como um impulso tangencial: a gravidade e aplicada apos a bola sair do canhao. Em voo, usa o parametro gravitacional terrestre e a lei do inverso do quadrado da distancia, integrada em passos de ate `0,05 s`. A escala do desenho e visual: `170 px` representam o raio medio real da Terra (`6.371 km`). A simulacao nao modela atmosfera, rotacao terrestre, variacoes locais da gravidade nem a massa/consumo de combustivel do canhao.
