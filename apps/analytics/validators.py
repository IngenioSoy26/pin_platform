def validate_prediction(prediction_obj):
    prediction_obj.is_validated = True
    prediction_obj.save()
    return True