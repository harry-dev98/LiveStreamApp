
from tensorflow.keras import models


def trainedModel(dataset):
    
    if dataset == "AlphaNum" or dataset == "alphaNum":
        arr = [models.load_model('./trainedModels/AlphaNumericTestAcc_9379_36Classes__TisTrouble.h5'),
               models.load_model('./trainedModels/AlphaNumericTestAcc_9337_36Classes__StudentsName.h5'),
               models.load_model('./trainedModels/AlphaNumericTestAcc_9307_36Classes__ALLok.h5'),
               models.load_model('./trainedModels/AlphaNumericTestAcc_924_36Classes__bigFilters.h5'),
              ]
        return arr