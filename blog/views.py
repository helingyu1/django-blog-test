import markdown

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from comments.forms import CommentForm
from .models import Post,Category
from django.views.generic import ListView,DetailView
from django.core.paginator import Paginator

# Create your views here.

def index(request):
    post_list = Post.objects.all()
    return render(request,'blog/index.html',context={'post_list':post_list})

def detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    
    post.increase_views()
    
    post.body = markdown.markdown(post.body,
                                  extensions=[
                                      'markdown.extensions.extra',
                                      'markdown.extensions.codehilite',
                                      'markdown.extensions.toc',
                                  ])
    # 记得在顶部导入 CommentForm
    form = CommentForm()
    # 获取这篇 post 下的全部评论
    comment_list = post.comment_set.all()

    # 将文章、表单、以及文章下的评论列表作为模板变量传给 detail.html 模板，以便渲染相应数据。
    context = {'post': post,
               'form': form,
               'comment_list': comment_list
               }
    return render(request, 'blog/detail.html', context=context)

def category(request, pk):
    cate = get_object_or_404(Category, pk=pk)
    post_list = Post.objects.filter(category=cate).order_by('-created_time')
    return render(request, 'blog/index.html', context={'post_list': post_list})

def archives(request, year, month):
    post_list = Post.objects.filter(created_time__year=year,
                                    created_time__month=month
                                    ).order_by('-created_time')
    return render(request, 'blog/index.html', context={'post_list': post_list})
    
    
class IndexView(ListView):
    model = Post
    template_name = 'blog/index.html'
    context_object_name = 'post_list'
    paginate_by = 3
    
    def get_context_data(self, **kwargs):
        """
        在视图函数中将模板变量传递给模板是通过给 render 函数的 context 参数传递一个字典实现的，
        例如 render(request, 'blog/index.html', context={'post_list': post_list})，
        这里传递了一个 {'post_list': post_list} 字典给模板。
        在类视图中，这个需要传递的模板变量字典是通过 get_context_data 获得的，
        所以我们复写该方法，以便我们能够自己再插入一些我们自定义的模板变量进去。
        """
        # 首先获得父类生成的传递给模板的字典
        context = super().get_context_data(**kwargs)
        
        # 父类生成的字典中已有 paginator、page_obj、is_paginated 三个模板变量，
        # paginator 是 Paginator 的一个实例，
        # page_obj 是 Page 的一个实例，
        # is_paginated 是一个布尔变量，用于指示是否已分页。
        # 例如如果规定每页 10 个数据，而本身只有5个数据，其实就用不着分页，此时 is_paginated=False.
        # 由于 context 是一个字典，所以调用 get 方法从中取出某个键对应的值。
        paginator = context.get('paginator')
        page = context.get('page_obj')
        is_paginated = context.get('is_paginated')
        
        # 调用自己写的 pagination_data 方法获得显示分页导航条需要的数据，见下方。
        pagination_data = self.pagination_data(paginator, page, is_paginated)
        
        # 将分页导航条的模板变量更新到 context 中，注意 pagination_data 方法返回的也是一个字典。
        context.update(pagination_data)
        
        # 将更新后的 context 返回，以便 ListView 使用这个字典中的模板变量去渲染模板。
        # 注意此时 context 字典中已有了显示分页导航条所需的数据。
        return context
    
    def pagination_data(self, paginator, page, is_paginated):
        if not is_paginated:
            # 如果没有分页，则无需显示分页导航条，不用任何分页导航条数据，因此返回一个空的字典。
                return {}
                
        # 当前页左边连续的页码号，初始值为空
        left = []
        
        # 当前页右边连续的页码号，初始值为空
        right = []
        
        # 标识第一页页码后面是否需要显示省略号
        left_has_more = False
        
        # 标识最后一页页码前是否需要省略号
        right_has_more = False
        
        # 标识是否需要显示第一页的页码号。
        # 因为如果当前页左边的连续页码号中已经含有第一页的页码号，此时就无须再显示第一页的页码号，
        # 其他情况下第一页的页码号是始终需要显示的。
        # 初始值为 False
        first = False
        
        # 标识是否需要显示最后一页的页码号
        # 需要此指示变量的理由和上面相同
        last = False
        
        # 获得用户当前请求的页码号
        page_number = page.number
        
        # 获得分页后的总页数
        total_pages = paginator.num_pages
        
        #获得整个分页页码列表，比如分了四页，那么就是[1,2,3,4]
        page_range = paginator.page_range
        
        if page_number == 1:
            # 如果用户请求的是第一的数据，那么当前页面左边的不需要数据，因此 left=[]
            # 此时只要获取当前页面右边的连续页码号，
            # 比如分页页码列表是[1,2,3,4],那么获取的就是 right=[2,3].
            # 注意这里只获取了当前页码后续梁旭两个页码，你可以更改这个数字以获取更多页码。
            right = page_range[page_number:page_number + 2]
            
            # 如果最右边的页号码比最后一页的号码-1还要小，
            # 说明最右边的页码号和最后一页的页号码之间还有其他页码，因此需要显示省略号，通过 right_has_more 来指示
            if right[-1] < total_pages - 1:
                right_has_more = True
                
            # 如果最右边的页码号比最后一页的页码号小，说明当前页右边的连续号码中不含有最后一页的号码
            # 所以需要显示最后一页的页号码，通过 last 来只是
            if right[-1] < total_pages:
                last = True
                
        elif page_number == total_pages:
            # 如果用户请求的是最后一页的数据，
            # 此时只要获取当前页左边的连续页码号。
            # 比如分页页码列表是[1,2,3,4]，那么获取的就是 left = [2,3]
            # ...
            left = page_range[(page_number - 3) if (page_number - 3) > 0 else 0:page_number - 1]
            
            # 如果最左边的页号码比第二页页号码还大，
            # 说明最左边的页号码和第一页的页号码之间还有其他页码，因此需要显示省略号，通过 left_has_more=True标识
            if left[0] > 2:
                left_has_more = True
            
            # 如果最左边的页码号比第一页的页码号大，说明当前页左边的连续号码也中不包含第一页，
            # 所以需要显示第一页的页码号，通过first 来标识
            if left[0] > 1:
                first = True
        
        else:
            # 用户请求的既不是最后一页，也不是第一页，则需要获取当前页左右两边的连续页码号，
            # 这里只获取了当前页码前后连续两个页码。
            left = page_range[(page_number - 3) if (page_number - 3) > 0 else 0:page_number - 1]
            right = page_range[page_number:page_number + 2]
            
            # 是否需要显示最后一页和最后一页钱的省略号
            if right[-1] < total_pages - 1:
                right_has_more = True
            if right[-1] < total_pages:
                last = True
                
            # 是否需要显示第一页和第一页后的省略号
            if left[0] > 2:
                left_has_more = True
            if left[0] > 1:
                first = True
                
        data = {
            'left' : left,
            'right' : right,
            'left_has_more' : left_has_more,
            'right_has_more' : right_has_more,
            'first' : first,
            'last' : last,        
        }
        
        return data
            