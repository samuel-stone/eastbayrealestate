
def analyze_property(property_data):

    score = 0


    if property_data.get(
        "price"
    ):

        score += 10


    if property_data.get(
        "location"
    ):

        score += 20


    return {

        "score":
            score,

        "recommendation":
            "review"

    }
