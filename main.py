#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import webapp2
import os
import re
import jinja2

from string import letters
from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext import webapp

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = True)

def render_str(template, **params):
	t = jinja_env.get_template(template)
	return t.render(params)


class MainHandler(webapp2.RequestHandler):
    def write(self, *a, **kw):
    	self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
    	return render_str(template, **params)

    def render(self, template, **kw):
    	self.write(self.render_str(template, **kw))



class NewPost(MainHandler):
	""" NewPost
	render form for new post"""

	def get(self):
		user = users.get_current_user()
		
	
		if user:
			user_name = users.get_current_user().nickname()
			user_id = users.get_current_user().user_id()
			posts = db.GqlQuery("select * from Post where user_id = :1 order by created desc", user_id)



			self.render("newpost.html", user_name = user_name, posts = posts)
		else:
			self.redirect("/login")

	def post(self):
		user = users.get_current_user()
		user_id = users.get_current_user().user_id()
		user_name = users.get_current_user().nickname()

		if not user:
			self.redirect("/login")
		else:
			subject = self.request.get('subject')
			content = self.request.get('content')


		if subject and content:
			p = Post(subject = subject, content = content, user_id = user_id, user_name = user_name)
			p.put()
			#self.redirect('/')
			post_key = p.put()
			self.redirect("/%s" %post_key.id())#use regular exfor handler and use subject as url 
		
		else:
			error = "subject and content please"
			self.render("newpost.html", subject=subject, content= content, error= error,  user_name = user_name)

class EditPost(MainHandler):

	def get(self,post_id):
		user = users.get_current_user()
		if not user:
			self.redirect("/login")
		else:
			key = db.Key.from_path('Post', int(post_id))
			post = db.get(key)
			self.render("newpost.html",subject=post.subject, content= post.content)

	def post(self,post_id):
		user_id = users.get_current_user().user_id()
		user_name = users.get_current_user().nickname()

		subject = self.request.get('subject')
		content = self.request.get('content')
		
		if subject and content:
			key = db.Key.from_path('Post', int(post_id))
			post = db.get(key)

			post = Post(subject = subject, content = content, user_id = user_id, user_name = user_name)
			post.put()
			post_id = post.put()
			#self.redirect('/')
			self.redirect("/%s" %post_id.id())#use regular exfor handler and use subject as url 
		
		else:
			error = "subject and content please"
			self.render("newpost.html", subject=subject, content= content, error= error,  user_name = user_name)
class DeletePost(MainHandler):

	def get(self,post_id):
		#user = users.get_current_user()
		if not users.is_current_user_admin():
			self.redirect("/login")
		else:
			key = db.Key.from_path('Post', int(post_id))
			db.delete(key)
			self.redirect("/" )

class Post(db.Model): #create database object for a post

	subject = db.StringProperty(required = True)
	content = db.TextProperty(required = True)
	created = db.DateTimeProperty(auto_now_add = True)
	user_id = db.StringProperty(required = True)
	user_name = db.StringProperty(required = True)



class PostPage(MainHandler):

	def get(self, post_id):
		key = db.Key.from_path('Post', int(post_id))
		post = db.get(key)

		if not post:
			self.error(404)
			return
		self.render("postpage.html", post = post)



class Front(MainHandler):
	def get(self):
		posts = db.GqlQuery("select * from Post order by created desc limit 10")
		self.render("front.html", posts = posts)

class Admin(MainHandler):

	def get(self):
		user = users.get_current_user()

		if user:
			user_id = users.get_current_user().user_id()
			user_name = users.get_current_user().nickname()
			posts = db.GqlQuery("select * from Post where user_id = :1 order by created desc", user_id)
			self.render("admin.html", posts = posts, user_name = user_name)
		else:
			self.redirect("/login")

class Login(MainHandler):
	def get(self):
		user = users.get_current_user()
		if user:
			greeting = ("Welcome, %s! (<a href=\"%s\">sign out</a>)" % (user.nickname(), users.create_logout_url("/")))
		else:
			greeting = ("<a href=\"%s\">Sign in or register</a>." % users.create_login_url("/"))

		self.write("<html><body>%s</body></html>" % greeting)


		
app = webapp2.WSGIApplication([
    						('/', Front),
							('/newpost', NewPost),
							('/edit/([0-9]+)', EditPost),
							('/delete/([0-9]+)', DeletePost),
							('/admin', Admin),
							('/login', Login),
							('/([0-9]+)', PostPage),
							], debug=True)
