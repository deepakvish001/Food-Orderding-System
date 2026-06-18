from django.shortcuts import render
from rest_framework.decorators import api_view
from django.contrib.auth import authenticate
from rest_framework.response import Response
from .models import *

@api_view(['POST'])
def admin_login_api(request):
 username = request.data.get('username')
 password = request.data.get('password')

 user = authenticate(username=username, password=password)
 if user is not None and user.is_staff:
  return Response({"message":"Login successful","username":username}, status=200)
 return Response({"message":"Invalid Credentials"}, status=401)
 
@api_view(['POST']) 
def add_category(request):
 category_name = request.data.get('category_name')

 Category.objects.create(category_name=category_name)
 return Response({"message":"Category has been created"}, status=201)
 
 
from .serializers import CategorySerializer 
@api_view(['GET']) 
def list_category(request):
 categories = Category.objects.all()
 serializer = CategorySerializer(categories,many=True)
 return Response(serializer.data)


from rest_framework.parsers import MultiPartParser, FormParser  #used for handling multi-type data
from rest_framework.decorators import parser_classes
from .serializers import FoodSerializer
@api_view(['POST']) 
@parser_classes([MultiPartParser, FormParser])
def add_food_item(request):
 serializer = FoodSerializer(data = request.data)
 if serializer.is_valid():
  serializer.save()
  return Response({"message":"Food item has been added"}, status=201)
 return Response({"mesaage":"Something went Wrong", "errors":serializer.errors}, status=400) 
 

@api_view(['GET']) 
def list_food(request): 
 foods = Food.objects.all()
 serializer = FoodSerializer(foods,many=True)
 return Response(serializer.data)


@api_view(['GET']) 
def food_search(request): 
 query = request.GET.get('q','')
 foods = Food.objects.filter(item_name__icontains=query)
 serializer = FoodSerializer(foods,many=True)
 return Response(serializer.data)


import random
@api_view(['GET'])
def random_foods(request):
 foods = list(Food.objects.all())
 random.shuffle(foods)
 limited_foods = foods[0:9]
 serializer = FoodSerializer(limited_foods, many=True)
 return Response(serializer.data)
 
 
from django.contrib.auth.hashers import make_password
@api_view(['POST'])
def register_user(request):
 first_name = request.data.get('first_name')
 last_name = request.data.get('last_name')
 email = request.data.get('email')
 mobile = request.data.get('mobile')
 password = request.data.get('password')
 
 if User.objects.filter(email=email).exists() or User.objects.filter(mobile=mobile).exists():
  return Response({"message":"Email or mobile already registered!"}, status=400)
 
 User.objects.create(first_name=first_name, last_name=last_name,email=email, mobile=mobile, password=make_password(password)) 
 return Response({"message":"User registered successfully"}, status=201)

 
from django.db.models import Q 
from django.contrib.auth.hashers import check_password
@api_view(['POST'])
def login_user(request):
 identifier = request.data.get('emailCon')
 password = request.data.get('password')
 try : 
  user = User.objects.get(Q(email=identifier) | Q(mobile=identifier))
  if check_password(password, user.password):
   return Response({"message":"Login Successful!", "userId":user.id, "userName":f"{user.first_name} {user.last_name}"}, status=200)
  else :
   return Response({"message":"Invalid Credentials"}, status=401)
 except:
  return Response({"message":"Invalid Credentials"}, status=401)
  
 
from django.shortcuts import get_object_or_404   
@api_view(['GET'])
def food_detail(request, id):
 # food = Food.objects.get(id=id)
 food = get_object_or_404(Food, id=id)
 serializer = FoodSerializer(food)
 return Response(serializer.data)
 

@api_view(['POST']) 
def add_to_cart(request):
  user_id = request.data.get('userId')
  food_id = request.data.get('foodId')
  try:
    user = User.objects.get(id=user_id)
    food = Food.objects.get(id=food_id)
    order, created = Order.objects.get_or_create(
      user=user,
      food=food,
      is_order_placed=False,
      defaults={'quantity': 1}
    )
    if not created:
      order.quantity += 1
      order.save()
    return Response({"message":"Food added to cart successfully!"}, status=200)
  except:
    return Response({"message":"Something went wrong!"},status=404)  
    

from .serializers import CartOrderSerializer
@api_view(['GET']) 
def get_cart_items(request, user_id):
  orders = Order.objects.filter(user_id=user_id, is_order_placed=False).select_related('food')
  serializer = CartOrderSerializer(orders, many=True)
  return Response(serializer.data)


@api_view(['PUT'])
def update_cart_quantity(request):
  order_id = request.data.get('orderId')
  quantity = request.data.get('quantity')
  try:
    order = Order.objects.get(id=order_id, is_order_placed=False)
    order.quantity = quantity
    order.save()
    return Response({"message":"quantity updated successfully"},status=200)
  except:
    return Response({"message":"Something went wrong!"}, status=400)  

    
@api_view(['DELETE'])  
def delete_cart_item(request, order_id):
  try:
    order = Order.objects.get(id=order_id, is_order_placed=False)
    order.delete()
    return Response({"message":"Item deleted from cart"},status=200)
  except:
    return Response({"message":"Somthing went wrong!"}, status=404) 

  
def make_unique_order_number():
  while True:
    num = str(random.randint(100000000,999999999)) 
    if not OrderAddress.objects.filter(order_number=num).exists():
      return num 
     
@api_view(['POST'])  
def place_order(request):
  user_id = request.data.get('userId')  
  address =  request.data.get('address')
  payment_mode =  request.data.get('paymentMode')
  card_number =  request.data.get('cardNumber')
  expiry =  request.data.get('expiry')
  cvv =  request.data.get('cvv')

  try:
    order = Order.objects.filter(user_id=user_id, is_order_placed=False)
    if not order.exists():
            return Response({"message": "No pending orders found."}, status=404)
    order_number = make_unique_order_number()
    order.update(order_number=order_number,is_order_placed=True)
    OrderAddress.objects.create(
      user_id = user_id,
      order_number = order_number,
      address =  address
    )
    PaymentDetail.objects.create(
      user_id = user_id,
      order_number = order_number,
      payment_mode = payment_mode,
      card_number = card_number if payment_mode=='online' else None,
      expiry_date = expiry if payment_mode=='online' else None,
      cvv = cvv if payment_mode=='online' else None
    )
    return Response({"message":f'Order placed successfully! Order No : {order_number}'}, status=201)
  except:
    return Response({"message":"Something went wrong!"}, status=404)  


from .serializers import MyOrdersListSerializer
@api_view(['GET']) 
def user_orders(request, user_id):
  orders = OrderAddress.objects.filter(user_id=user_id).order_by('-id')
  serializer = MyOrdersListSerializer(orders, many=True)
  return Response(serializer.data)


from .serializers import OrderSerializer
@api_view(['GET'])
def order_by_order_number(request, order_number):
  orders = Order.objects.filter(order_number=order_number, is_order_placed=True).select_related('food')
  serializer = OrderSerializer(orders, many=True)
  return Response(serializer.data)


from .serializers import OrderAddressSerializer
@api_view(['GET'])
def order_by_order_address(request, order_number):
  address = OrderAddress.objects.get(order_number=order_number)
  serializer = OrderAddressSerializer(address)
  return Response(serializer.data)
  

from django.shortcuts import render
def get_invoice(request, order_number):
  orders = Order.objects.filter(order_number=order_number, is_order_placed=True).select_related('food')
  address = OrderAddress.objects.get(order_number=order_number)
  grand_total = 0
  order_data = []
  for order in orders:
    total_price = order.food.price * order.quantity 
    grand_total += total_price
    order_data.append({
      'food': order.food,
      'quantity': order.quantity,
      'total_price' : total_price
    })
  return render(request, 'invoice.html',{
    'order_number': order_number,
    'address': address,
    'grand_total': grand_total,
    'orders' : order_data
  })
    

from .serializers import UserSerializer
@api_view(['GET'])    
def get_user_profile(request, user_id):
  user = User.objects.get(id=user_id)
  serializer = UserSerializer(user)
  return Response(serializer.data)


@api_view(['PUT'])    
def update_user_profile(request, user_id):
  user = User.objects.get(id=user_id)
  serializer = UserSerializer(user, data=request.data, partial=True)
  if serializer.is_valid():
    serializer.save()
    return Response({"message":"Profile updated successfully"}, status=200)
  return Response(serializer.errors, status=400)


@api_view(['POST'])    
def change_password(request, user_id):
  current_password = request.data.get('current_password')
  new_password = request.data.get('new_password')
  user = User.objects.get(id=user_id)

  if not check_password(current_password, user.password):
    return Response({"message":"Current password is incorrect"}, status=400)

  user.password = make_password(new_password)
  user.save()
  return Response({"message":"Password changed successfully"}, status=200)


from .serializers import OrderSummarySerializer
@api_view(['GET'])
def orders_not_confirmed(request):
  orders = OrderAddress.objects.filter(order_final_status__isnull=True).order_by('-order_time')
  serializer = OrderSummarySerializer(orders, many=True)
  return Response(serializer.data)

  
@api_view(['GET'])
def orders_confirmed(request):
  orders = OrderAddress.objects.filter(order_final_status="Order Confirmed").order_by('-order_time')
  serializer = OrderSummarySerializer(orders, many=True)
  return Response(serializer.data)

  
@api_view(['GET'])
def food_being_prepared(request):
  orders = OrderAddress.objects.filter(order_final_status="Food being Prepared").order_by('-order_time')
  serializer = OrderSummarySerializer(orders, many=True)
  return Response(serializer.data)

@api_view(['GET'])
def food_pickup(request):
  orders = OrderAddress.objects.filter(order_final_status="Food Pickup").order_by('-order_time')
  serializer = OrderSummarySerializer(orders, many=True)
  return Response(serializer.data)


@api_view(['GET'])
def food_delivered(request):
  orders = OrderAddress.objects.filter(order_final_status="Food Delivered").order_by('-order_time')
  serializer = OrderSummarySerializer(orders, many=True)
  return Response(serializer.data)  


@api_view(['GET'])
def order_cancelled(request):
  orders = OrderAddress.objects.filter(order_final_status="Order Cancelled").order_by('-order_time')
  serializer = OrderSummarySerializer(orders, many=True)
  return Response(serializer.data)


@api_view(['GET'])
def all_orders(request):
  orders = OrderAddress.objects.all().order_by('-order_time')
  serializer = OrderSummarySerializer(orders, many=True)
  return Response(serializer.data)


@api_view(['POST'])
def order_between_dates(request):
  from_date = request.data.get('from_date')
  to_date = request.data.get('to_date')
  status = request.data.get('status')
  orders = OrderAddress.objects.filter(order_time__date__range=[from_date, to_date])
  if status == 'not_confirmed':
    orders = orders.filter(order_final_status__isnull=True)
  elif status != 'all':
    orders = orders.filter(order_final_status=status)  
  serializer = OrderSummarySerializer(orders.order_by('-order_time'), many=True)
  
  return Response(serializer.data)
  

from .serializers import FoodtrackingSerializer, OrderDetailSerializer, OrderFoodSerializer
@api_view(['GET'])
def view_order_detail(request, order_number):
  try:
    order_address = OrderAddress.objects.select_related('user').get(order_number=order_number)
    ordered_food = Order.objects.filter(order_number=order_number).select_related('food')
    tracking = FoodTracking.objects.filter(order__order_number=order_number)
  except:
    return Response({"error":"Something went wrong!"}, status=404)
  
  return Response({
    'order' : OrderDetailSerializer(order_address).data,
    'foods': OrderFoodSerializer(ordered_food, many=True).data,
    'tracking': FoodtrackingSerializer(tracking, many=True).data
  })
 
  
@api_view(['POST'])
def update_order_status(request):
  order_number = request.data.get('order_number')
  new_status = request.data.get('status')
  remark = request.data.get('remark')
  
  try:
    address = OrderAddress.objects.get(order_number=order_number)
    order = Order.objects.filter(order_number=order_number).first()
    if not order:
      return Response({'error':"Order not found!"},status=404)
    FoodTracking.objects.create(order=order, remark=remark, status=new_status, order_cancelled_by_user=False)  
    address.order_final_status = new_status
    address.save()
    return Response({'message':'Order status updated successfully!'},status=200)
  except OrderAddress.DoesNotExist:
    return Response({'error':'Invalid order number!'},status=400)


@api_view(['GET']) 
def search_orders(request): 
  query = request.GET.get('q','')
  if query:
   orders = OrderAddress.objects.filter(order_number__icontains=query).order_by('-order_time')
  else:
    orders = [] 
  serializer = OrderSummarySerializer(orders, many=True)
  return Response(serializer.data)


@api_view(['GET','PUT','DELETE']) 
def category_detail(request,id):
  try:
    category = Category.objects.get(id=id)
  except Category.DoesNotExist:
    return Response({'error':'Category Not Found!'},status=404)  
  
  if request.method == 'GET':
    serializer = CategorySerializer(category)
    return Response(serializer.data)
  elif request.method == 'PUT':
    serializer = CategorySerializer(category,data=request.data)
    if serializer.is_valid():
      serializer.save()
      return Response({'message':'Category Updated Successfully!'},status=200)  
  elif request.method == 'DELETE':
    category.delete()
    return Response({'message':'Category Deleted Successfully!'},status=200) 
    

@api_view(['DELETE'])  
def delete_food(request,id):
  try:
    food = Food.objects.get(id=id)
    food.delete()
    return Response({'message':'Food deleted successfully'},status=200)
  except Food.DoesNotExist:
    return Response({'error':'Food item Not Found!'},status=404)  
  

@api_view(['GET','PUT']) 
@parser_classes([MultiPartParser, FormParser])
def edit_food(request,id):
  try:
    food = Food.objects.get(id=id)
  except Food.DoesNotExist:
    return Response({'error':'Food item Not Found!'},status=404)  
  
  if request.method == 'GET':
    serializer = FoodSerializer(food)
    return Response(serializer.data)
  elif request.method == 'PUT':
    data = request.data.copy()
    if 'image' not in request.FILES:
      data['image'] = food.image
    if 'is_available' in data:
      data['is_available'] = data['is_available'].lower()=='true'   
    serializer = FoodSerializer(food,data=data, partial=True)
    if serializer.is_valid():
      serializer.save()
      return Response({'message':'Food item Updated Successfully!'},status=200)  
  

@api_view(['GET'])
def list_users(request):
  users = User.objects.all().order_by('-id')
  serializer = UserSerializer(users, many=True)
  return Response(serializer.data)


@api_view(['DELETE'])  
def delete_user(request,id):
  try:
    user = User.objects.get(id=id)
    user.delete()
    return Response({'message':'User deleted successfully'},status=200)
  except Food.DoesNotExist:
    return Response({'error':'User Not Found!'},status=404)  
  

from django.utils.timezone import now, timedelta, make_aware
from django.db.models import Sum, F
from datetime import datetime
@api_view(['GET'])
def dashboard_matrics(request):
  today = now()
  start_week = today - timedelta(days=today.weekday())
  start_month = today.replace(day=1)
  start_year = today.replace(month=1, day=1)
  
  def get_sales_total(start_date):
    aware_start = make_aware(datetime.combine(start_date, datetime.min.time()))
    paid_orders = PaymentDetail.objects.filter(payment_date__gte=aware_start).values_list('order_number',flat=True)
    total = Order.objects.filter(order_number__in=paid_orders).annotate(
      total_price = F('quantity') * F('food__price')
    ).aggregate(sale_amount=Sum('total_price'))['sale_amount'] or 0.0
    return round(total,2)
    
  data = {
    'total_orders': OrderAddress.objects.count(),
    'new_orders': OrderAddress.objects.filter(order_final_status__isnull=True).count(),
    'confirmed_orders': OrderAddress.objects.filter(order_final_status="Order Confirmed").count(),
    'food_preparing': OrderAddress.objects.filter(order_final_status="Food being Prepared").count(),
    'food_pickup': OrderAddress.objects.filter(order_final_status="Food Pickup").count(),
    'food_delivered': OrderAddress.objects.filter(order_final_status="Food Delivered").count(),
    'cancelled_orders': OrderAddress.objects.filter(order_final_status="Order Cancelled").count(),
    'total_users': User.objects.count(),
    'total_categories': Category.objects.count(),
    'total_reviews': Review.objects.count(),
    'total_wishlists': Wishlist.objects.count(), 
    'today_sales' : get_sales_total(today),
    'week_sales' : get_sales_total(start_week),
    'month_sales' : get_sales_total(start_month),
    'year_sales' : get_sales_total(start_year),
  }
  return Response(data)



from decimal import Decimal
from collections import defaultdict
from django.db.models import Sum, F, DecimalField, Value
from django.db.models.functions import TruncMonth, Coalesce
@api_view(['GET'])
def mothly_sales_summary(request):
  # step 1 - pre-order total = Sum(quantity * price)
  orders = (
    Order.objects
    .filter(is_order_placed=True)
    .values('order_number')
    .annotate(
      total_price=Coalesce(
        Sum(
          F('quantity') * F('food__price'), 
          output_field=DecimalField(max_digits=12,decimal_places=2)
          ),
        Value(Decimal('0.00')),
        output_field=DecimalField(max_digits=12, decimal_places=2)
    )
  ))

  # step 2 - 
  order_price_map = {
    o['order_number'] : o['total_price'] for o in orders
  }
  
  # step 3 - month resolve
  addresses = (
    OrderAddress.objects
    .filter(order_number__in=order_price_map.keys())
    .annotate(month=TruncMonth('order_time'))
    .values('month','order_number')
  )
  
  month_totals = defaultdict(lambda: Decimal('0.00'))

  for addr in addresses:
    label = addr['month'].strftime('%b')
    month_totals[label] += order_price_map.get(addr['order_number'], Decimal(0.00))
  
  result = [{'month':m,"sales":float(total)} for m,total in month_totals.items()]  
  return Response(result)



@api_view(['GET'])
def top_selling_foods(request):
  top_food = (
    Order.objects
    .filter(is_order_placed=True)
    .values('food__item_name')
    .annotate(total_sold=Sum('quantity'))
    .order_by('-total_sold')[:5]
  )
  return Response(top_food)



from django.db.models.functions import TruncWeek
@api_view(['GET'])
def weekly_sales_summary(request):
  orders = (
    Order.objects
    .filter(is_order_placed=True)
    .values('order_number')
    .annotate(
      total_price=Coalesce(
        Sum(
          F('quantity') * F('food__price'), 
          output_field=DecimalField(max_digits=12,decimal_places=2)
          ),
        Value(Decimal('0.00')),
        output_field=DecimalField(max_digits=12, decimal_places=2)
    )
  ))

  order_price_map = {
    o['order_number'] : o['total_price'] for o in orders
  }
  
  addresses = (
    OrderAddress.objects
    .filter(order_number__in=order_price_map.keys())
    .annotate(week=TruncWeek('order_time'))
    .values('week','order_number')
  )
  
  week_totals = defaultdict(lambda: Decimal('0.00'))

  for addr in addresses:
    label = addr['week'].strftime('%W')
    week_totals[label] += order_price_map.get(addr['order_number'], Decimal(0.00))
  
  result = [{'week':w,"sales":float(total)} for w,total in week_totals.items()]  
  return Response(result)



from django.db.models import Count
@api_view(['GET'])
def weekly_user_registration(request):
  data = (
    User.objects
    .annotate(week=TruncWeek('reg_date'))
    .values('week')
    .annotate(new_users = Count('id'))
    .order_by('week')
  )
  
  result = [
    {'week':entry['week'].strftime('Week %W'),
     'new_users':entry['new_users']
    } 
    for entry in data
  ]  
  return Response(result)


@api_view(['POST']) 
def add_to_wishlist(request):
 user_id = request.data.get('user_id')
 food_id = request.data.get('food_id')
 
 obj, created = Wishlist.objects.get_or_create(user_id=user_id,food_id=food_id)
 if created:
  return Response({"message":"Added to wishlist"}, status=201)
 else: 
  return Response({"message":"Already in wishlist"}, status=200)
 

@api_view(['POST']) 
def remove_from_wishlist(request):
 user_id = request.data.get('user_id')
 food_id = request.data.get('food_id')
 try:
   Wishlist.objects.get(user_id=user_id, food_id=food_id).delete()
   return Response({"message":"Removed from wishlist"}, status=200)
 except Wishlist.DoesNotExist: 
   return Response({"message":"Item not found in wishlist"}, status=404)
 

from .serializers import WishlistSerializer
@api_view(['GET']) 
def get_to_wishlist(request,user_id):
  wishlist_items = Wishlist.objects.filter(user_id=user_id)
  serializer = WishlistSerializer(wishlist_items, many=True)
  return Response(serializer.data)
 

from .serializers import FoodtrackingSerializer
@api_view(['GET']) 
def track_order(request, order_number):
  sample_order = Order.objects.filter(
        order_number=order_number,
        is_order_placed=True
    )

  if not sample_order.exists():
    return Response({"message":"Order not found or not yet placed."}, status=404)
  
  tracking_entries = FoodTracking.objects.filter(
        order__in=sample_order
    ).order_by('status_date')
  serializer = FoodtrackingSerializer(tracking_entries, many=True)
  return Response(serializer.data)



@api_view(['POST'])
def cancel_order(request, order_number):
  remark = request.data.get('remark')
  address = OrderAddress.objects.get(order_number=order_number)
  sample_order = Order.objects.filter(order_number=order_number).first()
  FoodTracking.objects.create(
    order = sample_order,
    remark = remark,
    status = 'Order Cancelled',
    order_cancelled_by_user = True
  )
  address.order_final_status = 'Order Cancelled'
  address.save()
  return Response({'message':'Order Cancelled Successfully'},status=200)
  

@api_view(['POST']) 
def add_review(request, food_id):
  user_id = request.data.get('user_id')
  rating = request.data.get('rating')
  comment = request.data.get('comment')
  try:
    user = User.objects.get(id=user_id)
    food = Food.objects.get(id = food_id)
  except (User.DoesNotExist, Food.DoesNotExist):
    return Response({'message':'User or Food not Found'}, status=404)
  Review.objects.create(
    user = user,
    food = food,
    rating = rating,
    comment = comment,
  )
  return Response({'message':'Review Submitted'}, status=201)



from .serializers import ReviewSerializer
@api_view(['GET'])
def food_reviews(request, food_id):
  reviews = Review.objects.filter(food_id = food_id).order_by('-created_at')
  serializer = ReviewSerializer(reviews, many=True)
  return Response(serializer.data)


@api_view(['DELETE','PUT'])
def reviews_detail(request, id):
  try :
   review = Review.objects.get(id=id)
  except Review.DoesNotExist:
    return Response({'message':'Review not found'},status=404) 
  
  if request.method == 'DELETE':
    review.delete()
    return Response({'message':'Review Deleted'},status=200)  
    
  if request.method == 'PUT':
    data = {'rating':request.data.get('rating',review.rating),
            'comment':request.data.get('comment',review.comment)}
    serializer = ReviewSerializer(review, data=data, partial=True)
    if serializer.is_valid():
      serializer.save()
      return Response({'message':'Review Updated'},status=200)  
    return Response(serializer.errors,status=400)  



from django.db.models import Count, Avg
from .serializers import ReviewSerializer
@api_view(['GET'])
def food_rating_summary(request, food_id):
  reviews = Review.objects.filter(food_id = food_id)
  rating_summary = reviews.values('rating').annotate(count = Count('rating')).order_by('-rating')
  average = reviews.aggregate(average = Avg('rating'))['average'] or 0
  total_reviews = reviews.count()
  return Response({
    'average' : round(average,1),
    'total_reviews' : total_reviews,
    'breakdown' : {
     entry['rating'] : entry['count'] for entry in rating_summary
    }
  })



from .serializers import ReviewSerializer
@api_view(['GET'])
def all_reviews(request):
  reviews = Review.objects.select_related('user','food').order_by('-created_at')
  serializer = ReviewSerializer(reviews, many=True)
  return Response(serializer.data)


@api_view(['DELETE'])
def delete_review(request, id):
  try:
    reviews = Review.objects.get(id=id)
    reviews.delete()
    return Response({'message':'Review deleted successfully'},status=200)
  except Review.DoesNotExist:
    return Response({'message':'Review not found'},status=404)
  
  

