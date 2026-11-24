def test_balance_has_tank_scales_and_real_receipt_flags(client):
    shown=client.get('/').get_data(as_text=True)
    assert '罐车收发双账' in shown and '1.400 kg' in shown and 'gauge-fill' in shown
    feature=client.get('/ops/readings').get_data(as_text=True)
    assert '仪表回卷证据' in feature and '真实回卷' in feature
