#coding:utf-8
from .models import Article
from django.shortcuts import render, get_object_or_404
from .forms import PostForm
from django.shortcuts import redirect
from django.http import Http404
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count
from .commons import cache_manager
from django.contrib.auth.decorators import login_required
from django.contrib.syndication.views import Feed
import markdown2
from collections import Counter
# Create your views here.


def get_tags():
    postsAll = Article.objects.annotate(num_comment=Count('id')).filter(
        published_date__isnull=False)
    tags = [str(p.category) for p in postsAll if str(p.category) != '']
    tags = Counter(tags)
    return tags


def post_list(request):
    postsAll = Article.objects.annotate(num_comment=Count('id')).filter(
        published_date__isnull=False).order_by('-published_date')
    # for p in postsAll:
    #     p.click = cache_manager.get_click(p)
    tags = [str(p.category) for p in postsAll if str(p.category) != '']
    tags = Counter(tags)
    paginator = Paginator(postsAll, 5)  # Show 10 contacts per page
    page = request.GET.get('page')
    posts = []
    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        posts = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        posts = paginator.page(paginator.num_pages)
    finally:
        for pp in posts:
            pp.text = markdown2.markdown(pp.text, extras=['fenced-code-blocks'], )
    return render(request, 'blog/post_list.html', {'posts': posts, 'page': True,
                                                   'tags': tags, 'date_list': date_list()})


def post_detail(request, pk):
    post = get_object_or_404(Article, pk=str(pk))
    post.text = markdown2.markdown(post.text, extras=['fenced-code-blocks'], )
    postsAll = Article.objects.annotate(num_comment=Count('id')).filter(
        published_date__isnull=False).order_by('-published_date')
    tags = [str(p.category) for p in postsAll if str(p.category) != '']
    tags = Counter(tags)
    if post.published_date == None:
        return render(request, 'blog/post_detail.html', {'post': post, 'tags': tags, 'date_list': date_list()})
    else:
        page_list = list(postsAll)
        if post == page_list[-1]:
            before_page = page_list[-2]
            after_page = None
        elif post == page_list[0]:
            before_page = None
            after_page = page_list[1]
        else:
            situ = page_list.index(post)
            before_page = page_list[situ-1]
            after_page = page_list[situ+1]
        return render(request, 'blog/post_detail.html',{'post': post, 'tags': tags,
                        'before_page': before_page, 'after_page': after_page, 'date_list': date_list()})


@login_required
def post_new(request):
    if request.method == "POST":
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('post_detail', pk=post.pk)
    else:
        form = PostForm()
    return render(request, 'blog/post_edit.html', {'form': form, 'tags': get_tags(), 'date_list': date_list()})


@login_required
def post_edit(request, pk):
    post = get_object_or_404(Article, pk=pk)
    if request.method == "POST":
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('post_detail', pk=post.pk)
    else:
        form = PostForm(instance=post)
    return render(request, 'blog/post_edit.html', {'form': form, 'tags': get_tags(), 'date_list': date_list()})


@login_required
def post_draft_list(request):
    posts = Article.objects.filter(published_date__isnull=True).order_by('-created_date')
    for pp in posts:
        pp.text = markdown2.markdown(pp.text, extras=['fenced-code-blocks'], )
    return render(request, 'blog/post_draft_list.html', {'posts': posts, 'tags': get_tags(), 'date_list': date_list()})


@login_required
def post_publish(request, pk):
    post = get_object_or_404(Article, pk=pk)
    post.publish()
    return redirect('post_detail', pk=pk)


@login_required
def post_remove(request, pk):
    post = get_object_or_404(Article, pk=pk)
    post.delete()
    return redirect('post_list')


def archives(request):
    try:
        post_list = Article.objects.all().filter(published_date__isnull=False).order_by('-published_date')
    except Article.DoesNotExist:
        raise Http404
    return render(request, 'blog/archives.html', {'post_list': post_list, 'error': False,
                                                  'tags': get_tags(), 'date_list': date_list()})


def about_me(request):
    return render(request, 'blog/aboutme.html', {'tags': get_tags(), 'date_list': date_list()})


def search_tag(request, tag):
    try:
        post_list = Article.objects.filter(category__iexact=tag).filter(
            published_date__isnull=False).order_by('-published_date')
        for pp in post_list:
            pp.text = markdown2.markdown(pp.text, extras=['fenced-code-blocks'], )
    except Article.DoesNotExist:
        raise Http404
    return render(request, 'blog/tag.html', {'post_list': post_list, 'tag': tag,
                                             'tags': get_tags(), 'date_list': date_list()})


class RSSFeed(Feed):
    title = "RSS feed - blog"
    link = "feeds/posts/"
    description = "RSS feed - blog posts"
    def items(self):
        return Article.objects.order_by('-published_date')
    def item_title(self, item):
        return item.title
    def item_pubdate(self, item):
        return item.published_date
    def item_description(self, item):
        return item.text
    def item_link(self, item):
        return reverse('post_detail', args=[item.id])


def blog_search(request):
    if 's' in request.GET:
        s = request.GET['s']
        if not s:
            return render(request, 'blog/post_list.html', {'tags': get_tags(), 'date_list': date_list()})
        else:
            post_list = Article.objects.filter(title__icontains = s).order_by('-published_date')
            post_num = len(post_list)
            if post_num == 0 :
                return render(request, 'blog/search.html', {'post_list': post_list, 'error': True, 'tags': get_tags(),
                                                            'date_list': date_list()})
            else:
                for pp in post_list:
                    pp.text = markdown2.markdown(pp.text, extras=['fenced-code-blocks'], )
                return render(request, 'blog/search.html', {'post_list': post_list, 'error': False, 'tags': get_tags(),
                                                            'post_num': post_num, 's': s, 'date_list': date_list()})
    return redirect('/')

def date_list():
    # date_list = Article.objects.datetimes('published_date', 'month', order='DESC')
    postsAll = Article.objects.annotate(num_comment=Count('id')).filter(
        published_date__isnull=False).order_by('-published_date')
    year_month_list = [(p.published_date.year, p.published_date.month) for p in postsAll]
    year_month_dict = Counter(year_month_list)
    date_list = [(key[0], key[1], year_month_dict[key]) for key in year_month_dict]
    date_list.sort(reverse=True)
    return date_list

def date_archives(request, y, m):
    posts = Article.objects.annotate(num_comment=Count('id')).filter(
        published_date__isnull=False, published_date__year=y,
        published_date__month=m).order_by('-published_date')
    for pp in posts:
        pp.text = markdown2.markdown(pp.text, extras=['fenced-code-blocks'], )
    return render(request, 'blog/post_list.html', {'posts': posts, 'list_header': True, 'year': y, 'month': m,
                                                   'tags': get_tags(), 'date_list': date_list()})
