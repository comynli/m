from .models import db, User
from m import Router
from m.utils import jsonify

router = Router(prefix='')


@router.route('/', methods=['POST'])
def home(ctx, request):
    name = request.json().get('name')
    user = User(name=name)
    db.session.add(user)
    try:
        db.session.commit()
    except Exception as e:
        print(e)
        db.session.rollback()


@router.route('/{name}', methods=['GET'])
def get(ctx, request):
    name = request.args.get('name')
    user = User.query.filter(User.name == name).first_or_404('user {} not exist'.format(name))
    return jsonify(code=200, user=user.dictify())

