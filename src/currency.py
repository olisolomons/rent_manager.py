def format_currency(amount, symbol='£'):
    if amount < 0:
        return f'-{format_currency(-amount, symbol)}'
    else:
        return f'{symbol}{amount / 100:.2f}'
