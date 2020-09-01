import datetime as dt


def year(request):
    this_year = dt.datetime.today().year
    return {
        'year': this_year,
    }
