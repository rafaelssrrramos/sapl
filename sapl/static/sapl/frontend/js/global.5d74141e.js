/*! For license information please see global.5d74141e.js.LICENSE.txt */
!function(e){function t(t){for(var o,i,s=t[0],l=t[1],c=t[2],d=0,h=[];d<s.length;d++)i=s[d],Object.prototype.hasOwnProperty.call(r,i)&&r[i]&&h.push(r[i][0]),r[i]=0;for(o in l)Object.prototype.hasOwnProperty.call(l,o)&&(e[o]=l[o]);for(u&&u(t);h.length;)h.shift()();return n.push.apply(n,c||[]),a()}function a(){for(var e,t=0;t<n.length;t++){for(var a=n[t],o=!0,s=1;s<a.length;s++){var l=a[s];0!==r[l]&&(o=!1)}o&&(n.splice(t--,1),e=i(i.s=a[0]))}return e}var o={},r={global:0},n=[];function i(t){if(o[t])return o[t].exports;var a=o[t]={i:t,l:!1,exports:{}};return e[t].call(a.exports,a,a.exports,i),a.l=!0,a.exports}i.m=e,i.c=o,i.d=function(e,t,a){i.o(e,t)||Object.defineProperty(e,t,{enumerable:!0,get:a})},i.r=function(e){"undefined"!=typeof Symbol&&Symbol.toStringTag&&Object.defineProperty(e,Symbol.toStringTag,{value:"Module"}),Object.defineProperty(e,"__esModule",{value:!0})},i.t=function(e,t){if(1&t&&(e=i(e)),8&t)return e;if(4&t&&"object"==typeof e&&e&&e.__esModule)return e;var a=Object.create(null);if(i.r(a),Object.defineProperty(a,"default",{enumerable:!0,value:e}),2&t&&"string"!=typeof e)for(var o in e)i.d(a,o,function(t){return e[t]}.bind(null,o));return a},i.n=function(e){var t=e&&e.__esModule?function(){return e.default}:function(){return e};return i.d(t,"a",t),t},i.o=function(e,t){return Object.prototype.hasOwnProperty.call(e,t)},i.p="/static/sapl/frontend/";var s=window.webpackJsonp=window.webpackJsonp||[],l=s.push.bind(s);s.push=t,s=s.slice();for(var c=0;c<s.length;c++)t(s[c]);var u=l;n.push([0,"chunk-vendors"]),a()}({0:function(e,t,a){e.exports=a("c7e5")},"183e":function(e,t,a){(function(e){var t=a("7037");!function(e){e.Jcrop=function(a,o){function r(e){return Math.round(e)+"px"}function n(e){return I.baseClass+"-"+e}function i(){return e.fx.step.hasOwnProperty("backgroundColor")}function s(t){var a=e(t).offset();return[a.left,a.top]}function l(e){return[e.pageX-S[0],e.pageY-S[1]]}function c(a){"object"!=t(a)&&(a={}),I=e.extend(I,a),e.each(["onChange","onSelect","onRelease","onDblClick"],(function(e,t){"function"!=typeof I[t]&&(I[t]=function(){})}))}function u(e,t,a){if(S=s(D),re.setCursor("move"===e?e:e+"-resize"),"move"===e)return re.activateHandlers(function(e){var t=e;return ne.watchKeys(),function(e){te.moveOffset([e[0]-t[0],e[1]-t[1]]),t=e,oe.update()}}(t),m,a);var o=te.getFixed(),r=d(e),n=te.getCorner(d(r));te.setPressed(te.getCorner(r)),te.setCurrent(n),re.activateHandlers(function(e,t){return function(a){if(I.aspectRatio)switch(e){case"e":case"w":a[1]=t.y+1;break;case"n":a[0]=t.x+1;break;case"s":a[0]=t.x+1}else switch(e){case"e":case"w":a[1]=t.y2;break;case"n":a[0]=t.x2;break;case"s":a[0]=t.x2}te.setCurrent(a),oe.update()}}(e,o),m,a)}function d(e){switch(e){case"n":return"sw";case"s":case"e":return"nw";case"w":return"ne";case"ne":return"sw";case"nw":return"se";case"se":return"nw";case"sw":return"ne"}}function h(e){return function(t){return!(I.disabled||"move"===e&&!I.allowMove||(S=s(D),W=!0,u(e,l(t)),t.stopPropagation(),t.preventDefault(),1))}}function p(e,t,a){var o=e.width(),r=e.height();o>t&&t>0&&(o=t,r=t/e.width()*e.height()),r>a&&a>0&&(r=a,o=a/e.height()*e.width()),G=e.width()/o,K=e.height()/r,e.width(o).height(r)}function f(e){return{x:e.x*G,y:e.y*K,x2:e.x2*G,y2:e.y2*K,w:e.w*G,h:e.h*K}}function m(e){var t=te.getFixed();t.w>I.minSelect[0]&&t.h>I.minSelect[1]?(oe.enableHandles(),oe.done()):oe.release(),re.setCursor(I.allowSelect?"crosshair":"default")}function g(e){if(I.disabled)return!1;if(!I.allowSelect)return!1;W=!0,S=s(D),oe.disableHandles(),re.setCursor("crosshair");var t=l(e);return te.setPressed(t),oe.update(),re.activateHandlers(b,m,"touch"===e.type.substring(0,5)),ne.watchKeys(),e.stopPropagation(),e.preventDefault(),!1}function b(e){te.setCurrent(e),oe.update()}function v(){var t=e("<div></div>").addClass(n("tracker"));return P&&t.css({opacity:0,backgroundColor:"white"}),t}function w(e){y([e[0]/G,e[1]/K,e[2]/G,e[3]/K]),I.onSelect.call(ie,f(te.getFixed())),oe.enableHandles()}function y(e){te.setPressed([e[0],e[1]]),te.setCurrent([e[2],e[3]]),oe.update()}function C(){I.disabled=!0,oe.disableHandles(),oe.setCursor("default"),re.setCursor("default")}function x(){I.disabled=!1,_()}function k(e,t,a){var o=t||I.bgColor;I.bgFade&&i()&&I.fadeTime&&!a?e.animate({backgroundColor:o},{queue:!1,duration:I.fadeTime}):e.css("backgroundColor",o)}function _(e){I.allowResize?e?oe.enableOnly():oe.enableHandles():oe.disableHandles(),re.setCursor(I.allowSelect?"crosshair":"default"),oe.setCursor(I.allowMove?"move":"default"),I.hasOwnProperty("trueSize")&&(G=I.trueSize[0]/O,K=I.trueSize[1]/j),I.hasOwnProperty("setSelect")&&(w(I.setSelect),oe.done(),delete I.setSelect),ae.refresh(),I.bgColor!=Z&&(k(I.shade?ae.getShades():H,I.shade&&I.shadeColor||I.bgColor),Z=I.bgColor),$!=I.bgOpacity&&($=I.bgOpacity,I.shade?ae.refresh():oe.setBgOpacity($)),N=I.maxSize[0]||0,J=I.maxSize[1]||0,V=I.minSize[0]||0,U=I.minSize[1]||0,I.hasOwnProperty("outerImage")&&(D.attr("src",I.outerImage),delete I.outerImage),oe.refresh()}var S,I=e.extend({},e.Jcrop.defaults),A=navigator.userAgent.toLowerCase(),P=/msie/.test(A),T=/msie [1-6]\./.test(A);"object"!=t(a)&&(a=e(a)[0]),"object"!=t(o)&&(o={}),c(o);var z={border:"none",visibility:"visible",margin:0,padding:0,position:"absolute",top:0,left:0},F=e(a),R=!0;if("IMG"==a.tagName){if(0!=F[0].width&&0!=F[0].height)F.width(F[0].width),F.height(F[0].height);else{var M=new Image;M.src=F[0].src,F.width(M.width),F.height(M.height)}var D=F.clone().removeAttr("id").css(z).show();D.width(F.width()),D.height(F.height()),F.after(D).hide()}else D=F.css(z).show(),R=!1,null===I.shade&&(I.shade=!0);p(D,I.boxWidth,I.boxHeight);var O=D.width(),j=D.height(),H=e("<div />").width(O).height(j).addClass(n("holder")).css({position:"relative",backgroundColor:I.bgColor}).insertAfter(F).append(D);I.addClass&&H.addClass(I.addClass);var L=e("<div />"),B=e("<div />").width("100%").height("100%").css({zIndex:310,position:"absolute",overflow:"hidden"}),E=e("<div />").width("100%").height("100%").css("zIndex",320),q=e("<div />").css({position:"absolute",zIndex:600}).dblclick((function(){var e=te.getFixed();I.onDblClick.call(ie,e)})).insertBefore(D).append(B,E);R&&(L=e("<img />").attr("src",D.attr("src")).css(z).width(O).height(j),B.append(L)),T&&q.css({overflowY:"hidden"});var N,J,V,U,G,K,W,Y,Q=I.boundary,X=v().width(O+2*Q).height(j+2*Q).css({position:"absolute",top:r(-Q),left:r(-Q),zIndex:290}).mousedown(g),Z=I.bgColor,$=I.bgOpacity;S=s(D);var ee=function(){function e(){var e,t={},a=["touchstart","touchmove","touchend"],o=document.createElement("div");try{for(e=0;e<a.length;e++){var r=a[e],n=(r="on"+r)in o;n||(o.setAttribute(r,"return;"),n="function"==typeof o[r]),t[a[e]]=n}return t.touchstart&&t.touchend&&t.touchmove}catch(e){return!1}}return{createDragger:function(e){return function(t){return!(I.disabled||"move"===e&&!I.allowMove||(S=s(D),W=!0,u(e,l(ee.cfilter(t)),!0),t.stopPropagation(),t.preventDefault(),1))}},newSelection:function(e){return g(ee.cfilter(e))},cfilter:function(e){return e.pageX=e.originalEvent.changedTouches[0].pageX,e.pageY=e.originalEvent.changedTouches[0].pageY,e},isSupported:e,support:!0===I.touchSupport||!1===I.touchSupport?I.touchSupport:e()}}(),te=function(){function e(){if(!I.aspectRatio)return function(){var e,t=l-i,r=c-s;return N&&Math.abs(t)>N&&(l=t>0?i+N:i-N),J&&Math.abs(r)>J&&(c=r>0?s+J:s-J),U/K&&Math.abs(r)<U/K&&(c=r>0?s+U/K:s-U/K),V/G&&Math.abs(t)<V/G&&(l=t>0?i+V/G:i-V/G),i<0&&(l-=i,i-=i),s<0&&(c-=s,s-=s),l<0&&(i-=l,l-=l),c<0&&(s-=c,c-=c),l>O&&(i-=e=l-O,l-=e),c>j&&(s-=e=c-j,c-=e),i>O&&(c-=e=i-j,s-=e),s>j&&(c-=e=s-j,s-=e),o(a(i,s,l,c))}();var e,t,r,n,u=I.aspectRatio,d=I.minSize[0]/G,h=I.maxSize[0]/G,p=I.maxSize[1]/K,f=l-i,m=c-s,g=Math.abs(f),b=Math.abs(m);return 0===h&&(h=10*O),0===p&&(p=10*j),g/b<u?(t=c,r=b*u,(e=f<0?i-r:r+i)<0?(e=0,n=Math.abs((e-i)/u),t=m<0?s-n:n+s):e>O&&(e=O,n=Math.abs((e-i)/u),t=m<0?s-n:n+s)):(e=l,n=g/u,(t=m<0?s-n:s+n)<0?(t=0,r=Math.abs((t-s)*u),e=f<0?i-r:r+i):t>j&&(t=j,r=Math.abs(t-s)*u,e=f<0?i-r:r+i)),e>i?(e-i<d?e=i+d:e-i>h&&(e=i+h),t=t>s?s+(e-i)/u:s-(e-i)/u):e<i&&(i-e<d?e=i-d:i-e>h&&(e=i-h),t=t>s?s+(i-e)/u:s-(i-e)/u),e<0?(i-=e,e=0):e>O&&(i-=e-O,e=O),t<0?(s-=t,t=0):t>j&&(s-=t-j,t=j),o(a(i,s,e,t))}function t(e){return e[0]<0&&(e[0]=0),e[1]<0&&(e[1]=0),e[0]>O&&(e[0]=O),e[1]>j&&(e[1]=j),[Math.round(e[0]),Math.round(e[1])]}function a(e,t,a,o){var r=e,n=a,i=t,s=o;return a<e&&(r=a,n=e),o<t&&(i=o,s=t),[r,i,n,s]}function o(e){return{x:e[0],y:e[1],x2:e[2],y2:e[3],w:e[2]-e[0],h:e[3]-e[1]}}var r,n,i=0,s=0,l=0,c=0;return{flipCoords:a,setPressed:function(e){e=t(e),l=i=e[0],c=s=e[1]},setCurrent:function(e){e=t(e),r=e[0]-l,n=e[1]-c,l=e[0],c=e[1]},getOffset:function(){return[r,n]},moveOffset:function(e){var t=e[0],a=e[1];0>i+t&&(t-=t+i),0>s+a&&(a-=a+s),j<c+a&&(a+=j-(c+a)),O<l+t&&(t+=O-(l+t)),i+=t,l+=t,s+=a,c+=a},getCorner:function(t){var a=e();switch(t){case"ne":return[a.x2,a.y];case"nw":return[a.x,a.y];case"se":return[a.x2,a.y2];case"sw":return[a.x,a.y2]}},getFixed:e}}(),ae=function(){function t(){return a(te.getFixed())}function a(e){h.top.css({left:r(e.x),width:r(e.w),height:r(e.y)}),h.bottom.css({top:r(e.y2),left:r(e.x),width:r(e.w),height:r(j-e.y2)}),h.right.css({left:r(e.x2),width:r(O-e.x2)}),h.left.css({width:r(e.x)})}function o(){return e("<div />").css({position:"absolute",backgroundColor:I.shadeColor||I.bgColor}).appendTo(d)}function n(){u||(u=!0,d.insertBefore(D),t(),oe.setBgOpacity(1,0,1),L.hide(),i(I.shadeColor||I.bgColor,1),oe.isAwake()?l(I.bgOpacity,1):l(1,1))}function i(e,t){k(c(),e,t)}function s(){u&&(d.remove(),L.show(),u=!1,oe.isAwake()?oe.setBgOpacity(I.bgOpacity,1,1):(oe.setBgOpacity(1,1,1),oe.disableHandles()),k(H,0,1))}function l(e,t){u&&(I.bgFade&&!t?d.animate({opacity:1-e},{queue:!1,duration:I.fadeTime}):d.css({opacity:1-e}))}function c(){return d.children()}var u=!1,d=e("<div />").css({position:"absolute",zIndex:240,opacity:0}),h={top:o(),left:o().height(j),right:o().height(j),bottom:o()};return{update:t,updateRaw:a,getShades:c,setBgColor:i,enable:n,disable:s,resize:function(e,t){h.left.css({height:r(t)}),h.right.css({height:r(t)})},refresh:function(){I.shade?n():s(),oe.isAwake()&&l(I.bgOpacity)},opacity:l}}(),oe=function(){function t(t){var a=e("<div />").css({position:"absolute",opacity:I.borderOpacity}).addClass(n(t));return B.append(a),a}function a(t,a){var o=e("<div />").mousedown(h(t)).css({cursor:t+"-resize",position:"absolute",zIndex:a}).addClass("ord-"+t);return ee.support&&o.bind("touchstart.jcrop",ee.createDragger(t)),E.append(o),o}function o(e){var t=I.handleSize,o=a(e,b++).css({opacity:I.handleOpacity}).addClass(n("handle"));return t&&o.width(t).height(t),o}function i(e){return a(e,b++).addClass("jcrop-dragbar")}function s(){var e=te.getFixed();te.setPressed([e.x,e.y]),te.setCurrent([e.x2,e.y2]),l()}function l(e){if(g)return c(e)}function c(e){var t=te.getFixed();(function(e,t){q.width(Math.round(e)).height(Math.round(t))})(t.w,t.h),function(e,t){I.shade||L.css({top:r(-t),left:r(-e)}),q.css({top:r(t),left:r(e)})}(t.x,t.y),I.shade&&ae.updateRaw(t),g||(q.show(),I.shade?ae.opacity($):u($,!0),g=!0),e?I.onSelect.call(ie,f(t)):I.onChange.call(ie,f(t))}function u(e,t,a){(g||t)&&(I.bgFade&&!a?D.animate({opacity:e},{queue:!1,duration:I.fadeTime}):D.css("opacity",e))}function d(){if(x=!0,I.allowResize)return E.show(),!0}function p(){x=!1,E.hide()}function m(e){e?(Y=!0,p()):(Y=!1,d())}var g,b=370,w={},y={},C={},x=!1;I.dragEdges&&e.isArray(I.createDragbars)&&function(e){var t;for(t=0;t<e.length;t++)C[e[t]]=i(e[t])}(I.createDragbars),e.isArray(I.createHandles)&&function(e){var t;for(t=0;t<e.length;t++)y[e[t]]=o(e[t])}(I.createHandles),I.drawBorders&&e.isArray(I.createBorders)&&function(e){var a,o;for(o=0;o<e.length;o++){switch(e[o]){case"n":a="hline";break;case"s":a="hline bottom";break;case"e":a="vline right";break;case"w":a="vline"}w[e[o]]=t(a)}}(I.createBorders),e(document).bind("touchstart.jcrop-ios",(function(t){e(t.currentTarget).hasClass("jcrop-tracker")&&t.stopPropagation()}));var k=v().mousedown(h("move")).css({cursor:"move",position:"absolute",zIndex:360});return ee.support&&k.bind("touchstart.jcrop",ee.createDragger("move")),B.append(k),p(),{updateVisible:l,update:c,release:function(){p(),q.hide(),I.shade?ae.opacity(1):u(1),g=!1,I.onRelease.call(ie)},refresh:s,isAwake:function(){return g},setCursor:function(e){k.css("cursor",e)},enableHandles:d,enableOnly:function(){x=!0},showHandles:function(){x&&E.show()},disableHandles:p,animMode:m,setBgOpacity:u,done:function(){m(!1),s()}}}(),re=function(){function t(t){X.css({zIndex:450}),t?e(document).bind("touchmove.jcrop",n).bind("touchend.jcrop",i):u&&e(document).bind("mousemove.jcrop",o).bind("mouseup.jcrop",r)}function a(){X.css({zIndex:290}),e(document).unbind(".jcrop")}function o(e){return s(l(e)),!1}function r(e){return e.preventDefault(),e.stopPropagation(),W&&(W=!1,c(l(e)),oe.isAwake()&&I.onSelect.call(ie,f(te.getFixed())),a(),s=function(){},c=function(){}),!1}function n(e){return s(l(ee.cfilter(e))),!1}function i(e){return r(ee.cfilter(e))}var s=function(){},c=function(){},u=I.trackDocument;return u||X.mousemove(o).mouseup(r).mouseout(r),D.before(X),{activateHandlers:function(e,a,o){return W=!0,s=e,c=a,t(o),!1},setCursor:function(e){X.css("cursor",e)}}}(),ne=function(){function t(e,t,a){I.allowMove&&(te.moveOffset([t,a]),oe.updateVisible(!0)),e.preventDefault(),e.stopPropagation()}var a=e('<input type="radio" />').css({position:"fixed",left:"-120px",width:"12px"}).addClass("jcrop-keymgr"),o=e("<div />").css({position:"absolute",overflow:"hidden"}).append(a);return I.keySupport&&(a.keydown((function(e){if(e.ctrlKey||e.metaKey)return!0;var a=!!e.shiftKey?10:1;switch(e.keyCode){case 37:t(e,-a,0);break;case 39:t(e,a,0);break;case 38:t(e,0,-a);break;case 40:t(e,0,a);break;case 27:I.allowSelect&&oe.release();break;case 9:return!0}return!1})).blur((function(e){a.hide()})),T||!I.fixedSupport?(a.css({position:"absolute",left:"-20px"}),o.append(a).insertBefore(D)):a.insertBefore(D)),{watchKeys:function(){I.keySupport&&(a.show(),a.focus())}}}();ee.support&&X.bind("touchstart.jcrop",ee.newSelection),E.hide(),_(!0);var ie={setImage:function(e,t){oe.release(),C();var a=new Image;a.onload=function(){var o=a.width,r=a.height,n=I.boxWidth,i=I.boxHeight;D.width(o).height(r),D.attr("src",e),L.attr("src",e),p(D,n,i),O=D.width(),j=D.height(),L.width(O).height(j),X.width(O+2*Q).height(j+2*Q),H.width(O).height(j),ae.resize(O,j),x(),"function"==typeof t&&t.call(ie)},a.src=e},animateTo:function(e,t){function a(){window.setTimeout(v,d)}var o=e[0]/G,r=e[1]/K,n=e[2]/G,i=e[3]/K;if(!Y){var s=te.flipCoords(o,r,n,i),l=te.getFixed(),c=[l.x,l.y,l.x2,l.y2],u=c,d=I.animationDelay,h=s[0]-c[0],p=s[1]-c[1],f=s[2]-c[2],m=s[3]-c[3],g=0,b=I.swingSpeed;o=u[0],r=u[1],n=u[2],i=u[3],oe.animMode(!0);var v=function(){g+=(100-g)/b,u[0]=Math.round(o+g/100*h),u[1]=Math.round(r+g/100*p),u[2]=Math.round(n+g/100*f),u[3]=Math.round(i+g/100*m),g>=99.8&&(g=100),g<100?(y(u),a()):(oe.done(),oe.animMode(!1),"function"==typeof t&&t.call(ie))};a()}},setSelect:w,setOptions:function(e){c(e),_()},tellSelect:function(){return f(te.getFixed())},tellScaled:function(){return te.getFixed()},setClass:function(e){H.removeClass().addClass(n("holder")).addClass(e)},disable:C,enable:x,cancel:function(){oe.done(),re.activateHandlers(null,null)},release:oe.release,destroy:function(){H.remove(),F.show(),F.css("visibility","visible"),e(a).removeData("Jcrop")},focus:ne.watchKeys,getBounds:function(){return[O*G,j*K]},getWidgetSize:function(){return[O,j]},getScaleFactor:function(){return[G,K]},getOptions:function(){return I},ui:{holder:H,selection:q}};return P&&H.bind("selectstart",(function(){return!1})),F.data("Jcrop",ie),ie},e.fn.Jcrop=function(t,a){var o;return this.each((function(){if(e(this).data("Jcrop")){if("api"===t)return e(this).data("Jcrop");e(this).data("Jcrop").setOptions(t)}else"IMG"==this.tagName?e.Jcrop.Loader(this,(function(){e(this).css({display:"block",visibility:"hidden"}),o=e.Jcrop(this,t),e.isFunction(a)&&a.call(o)})):(e(this).css({display:"block",visibility:"hidden"}),o=e.Jcrop(this,t),e.isFunction(a)&&a.call(o))})),this},e.Jcrop.Loader=function(t,a,o){var r=e(t),n=r[0];r.bind("load.jcloader",(function t(){n.complete?(r.unbind(".jcloader"),e.isFunction(a)&&a.call(n)):window.setTimeout(t,50)})).bind("error.jcloader",(function(t){r.unbind(".jcloader"),e.isFunction(o)&&o.call(n)})),n.complete&&e.isFunction(a)&&(r.unbind(".jcloader"),a.call(n))},e.Jcrop.defaults={allowSelect:!0,allowMove:!0,allowResize:!0,trackDocument:!0,baseClass:"jcrop",addClass:null,bgColor:"black",bgOpacity:.6,bgFade:!1,borderOpacity:.4,handleOpacity:.5,handleSize:null,aspectRatio:0,keySupport:!0,createHandles:["n","s","e","w","nw","ne","se","sw"],createDragbars:["n","s","e","w"],createBorders:["n","s","e","w"],drawBorders:!0,dragEdges:!0,fixedSupport:!0,touchSupport:null,shade:null,boxWidth:0,boxHeight:0,boundary:2,fadeTime:400,animationDelay:20,swingSpeed:3,minSelect:[0,0],maxSize:[0,0],minSize:[0,0],onChange:function(){},onSelect:function(){},onDblClick:function(){},onRelease:function(){}}}(e)}).call(this,a("1157"))},"332f":function(e,t,a){var o={"./pt-br":"d2d4","./pt-br.js":"d2d4"};function r(e){var t=n(e);return a(t)}function n(e){if(!a.o(o,e)){var t=new Error("Cannot find module '"+e+"'");throw t.code="MODULE_NOT_FOUND",t}return o[e]}r.keys=function(){return Object.keys(o)},r.resolve=n,e.exports=r,r.id="332f"},3551:function(e,t,a){(function(e,t){a("7db0"),a("a15b"),a("ac1f"),a("5319"),a("1276");var o=function(e){var t={};function a(e){return function(t){!function(e,t){t.data("size-warning")&&function(e,t){var a=t.siblings(".jcrop-holder"),o=t.data("min-width"),r=t.data("min-height");e.w<o||e.h<r?a.addClass("size-warning"):a.removeClass("size-warning")}(e,t),t.val(new Array(Math.round(e.x),Math.round(e.y),Math.round(e.x2),Math.round(e.y2)).join(","))}(t,e)}}return{init:function(){e("input.image-ratio").each((function(){var o=e(this),r=o.attr("name").replace(o.data("my-name"),o.data("image-field")),n=e("input.crop-thumb[data-field-name="+r+"]:first");if(n.length&&void 0!==n.data("thumbnail-url")){n.data("hide-field")&&n.hide().parents("div.form-row:first").hide();var i=o.attr("id")+"-image",s=n.data("org-width"),l=n.data("org-height"),c=o.data("min-width"),u=o.data("min-height"),d=l>s,h=u>c;if(!0===o.data("adapt-rotation")&&d!=h){var p=c;c=u,u=p}var f=e("<img>",{id:i,src:n.data("thumbnail-url")}),m={minSize:[5,5],keySupport:!1,trueSize:[s,l],onSelect:a(o),addClass:o.data("size-warning")&&(s<c||l<u)?"size-warning jcrop-image":"jcrop-image"};o.data("ratio")&&(m.aspectRatio=o.data("ratio")),o.data("box_max_width")&&(m.boxWidth=o.data("box_max_width")),o.data("box_max_height")&&(m.boxHeight=o.data("box_max_height"));var g,b=!1;if("-"==o.val()[0]&&(b=!0,o.val(o.val().substr(1))),o.val()?g=function(e){if(""!==e){var t=e.split(",");return[parseInt(t[0],10),parseInt(t[1],10),parseInt(t[2],10),parseInt(t[3],10)]}}(o.val()):(g=function(e,t,a,o){var r,n=e/t;return a<o*n?[0,r=Math.round((o-a/n)/2),a,o-r]:[r=Math.round((a-o*n)/2),0,a-r,o]}(c,u,s,l),o.val(g.join(","))),e.extend(m,{setSelect:g}),o.hide().after(f),e("#"+i).Jcrop(m,(function(){t[i]=this})),!0===o.data("allow-fullsize")){b&&(t[i].release(),o.val("-"+o.val()));var v="allow-fullsize-"+i,w=e('<div class="field-box allow-fullsize"><input type="checkbox" id="'+v+'" name="'+v+'"'+(b?"":' checked="checked"')+"></div>");o.parent().find(".help").length?w.insertBefore(o.parent().find(".help")):w.appendTo(o.parent()),e("#"+v).click((function(){!0===b?(o.val(o.val().substr(1)),t[i].setSelect(o.val().split(",")),b=!1):(o.val("-"+o.val()),t[i].release(),b=!0)})),o.parent().find(".jcrop-tracker").mousedown((function(){b&&(e("#"+v).attr("checked","checked"),b=!1)}))}}else o.hide().parents("div.form-row:first").hide()}))},jcrop:t}}(e);e((function(){t((function(){o.init()}))}))}).call(this,a("1157"),a("1157"))},"5abf":function(e,t,a){},"764b":function(e,t,a){"use strict";a("5abf"),a("e4b3"),a("183e"),a("3551")},acd2:function(e,t){tinymce.addI18n("pt_BR",{Redo:"Refazer",Undo:"Desfazer",Cut:"Recortar",Copy:"Copiar",Paste:"Colar","Select all":"Selecionar tudo","New document":"Novo documento",Ok:"Ok",Cancel:"Cancelar","Visual aids":"Ajuda visual",Bold:"Negrito",Italic:"Itálico",Underline:"Sublinhar",Strikethrough:"Riscar",Superscript:"Sobrescrito",Subscript:"Subscrever","Clear formatting":"Limpar formatação","Align left":"Alinhar à esquerda","Align center":"Centralizar","Align right":"Alinhar à direita",Justify:"Justificar","Bullet list":"Lista não ordenada","Numbered list":"Lista ordenada","Decrease indent":"Diminuir recuo","Increase indent":"Aumentar recuo",Close:"Fechar",Formats:"Formatos","Your browser doesn't support direct access to the clipboard. Please use the Ctrl+X/C/V keyboard shortcuts instead.":"Seu navegador não suporta acesso direto à área de transferência. Por favor use os atalhos Ctrl+X - C - V do teclado",Headers:"Cabeçalhos","Header 1":"Cabeçalho 1","Header 2":"Cabeçalho 2","Header 3":"Cabeçalho 3","Header 4":"Cabeçalho 4","Header 5":"Cabeçalho 5","Header 6":"Cabeçalho 6",Headings:"Cabeçalhos","Heading 1":"Cabeçalho 1","Heading 2":"Cabeçalho 2","Heading 3":"Cabeçalho 3","Heading 4":"Cabeçalho 4","Heading 5":"Cabeçalho 5","Heading 6":"Cabeçalho 6",Preformatted:"Preformatado",Div:"Div",Pre:"Pre",Code:"Código",Paragraph:"Parágrafo",Blockquote:"Aspas",Inline:"Em linha",Blocks:"Blocos","Paste is now in plain text mode. Contents will now be pasted as plain text until you toggle this option off.":"O comando colar está agora em modo texto plano. O conteúdo será colado como texto plano até você desligar esta opção.","Font Family":"Fonte","Font Sizes":"Tamanho",Class:"Classe","Browse for an image":"Procure uma imagem",OR:"OU","Drop an image here":"Arraste uma imagem aqui",Upload:"Carregar",Block:"Bloco",Align:"Alinhamento",Default:"Padrão",Circle:"Círculo",Disc:"Disco",Square:"Quadrado","Lower Alpha":"a. b. c. ...","Lower Greek":"α. β. γ. ...","Lower Roman":"i. ii. iii. ...","Upper Alpha":"A. B. C. ...","Upper Roman":"I. II. III. ...",Anchor:"Âncora",Name:"Nome",Id:"Id","Id should start with a letter, followed only by letters, numbers, dashes, dots, colons or underscores.":"Id deve começar com uma letra, seguido apenas por letras, números, traços, pontos, dois pontos ou sublinhados.","You have unsaved changes are you sure you want to navigate away?":"Você tem mudanças não salvas. Você tem certeza que deseja sair?","Restore last draft":"Restaurar último rascunho","Special character":"Caracteres especiais","Source code":"Código fonte","Insert/Edit code sample":"Inserir/Editar código de exemplo",Language:"Idioma","Code sample":"Exemplo de código",Color:"Cor",R:"R",G:"G",B:"B","Left to right":"Da esquerda para a direita","Right to left":"Da direita para a esquerda",Emoticons:"Emoticons","Document properties":"Propriedades do documento",Title:"Título",Keywords:"Palavras-chave",Description:"Descrição",Robots:"Robôs",Author:"Autor",Encoding:"Codificação",Fullscreen:"Tela cheia",Action:"Ação",Shortcut:"Atalho",Help:"Ajuda",Address:"Endereço","Focus to menubar":"Foco no menu","Focus to toolbar":"Foco na barra de ferramentas","Focus to element path":"Foco no caminho do elemento","Focus to contextual toolbar":"Foco na barra de ferramentas contextual","Insert link (if link plugin activated)":"Inserir link (se o plugin de link estiver ativado)","Save (if save plugin activated)":"Salvar (se o plugin de salvar estiver ativado)","Find (if searchreplace plugin activated)":"Procurar (se o plugin de procurar e substituir estiver ativado)","Plugins installed ({0}):":"Plugins instalados ({0}):","Premium plugins:":"Plugins premium:","Learn more...":"Saiba mais...","You are using {0}":"Você está usando {0}",Plugins:"Plugins","Handy Shortcuts":"Atalhos úteis","Horizontal line":"Linha horizontal","Insert/edit image":"Inserir/editar imagem","Image description":"Inserir descrição",Source:"Endereço da imagem",Dimensions:"Dimensões","Constrain proportions":"Manter proporções",General:"Geral",Advanced:"Avançado",Style:"Estilo","Vertical space":"Espaçamento vertical","Horizontal space":"Espaçamento horizontal",Border:"Borda","Insert image":"Inserir imagem",Image:"Imagem","Image list":"Lista de Imagens","Rotate counterclockwise":"Girar em sentido horário","Rotate clockwise":"Girar em sentido anti-horário","Flip vertically":"Virar verticalmente","Flip horizontally":"Virar horizontalmente","Edit image":"Editar imagem","Image options":"Opções de Imagem","Zoom in":"Aumentar zoom","Zoom out":"Diminuir zoom",Crop:"Cortar",Resize:"Redimensionar",Orientation:"Orientação",Brightness:"Brilho",Sharpen:"Aumentar nitidez",Contrast:"Contraste","Color levels":"Níveis de cor",Gamma:"Gama",Invert:"Inverter",Apply:"Aplicar",Back:"Voltar","Insert date/time":"Inserir data/hora","Date/time":"data/hora","Insert link":"Inserir link","Insert/edit link":"Inserir/editar link","Text to display":"Texto para mostrar",Url:"Url",Target:"Alvo",None:"Nenhum","New window":"Nova janela","Remove link":"Remover link",Anchors:"Âncoras",Link:"Link","Paste or type a link":"Cole ou digite um Link","The URL you entered seems to be an email address. Do you want to add the required mailto: prefix?":"The URL you entered seems to be an email address. Do you want to add the required mailto: prefix?","The URL you entered seems to be an external link. Do you want to add the required http:// prefix?":"A URL que você informou parece ser um link externo. Deseja incluir o prefixo http://?","Link list":"Lista de Links","Insert video":"Inserir vídeo","Insert/edit video":"Inserir/editar vídeo","Insert/edit media":"Inserir/editar imagem","Alternative source":"Fonte alternativa",Poster:"Autor","Paste your embed code below:":"Insira o código de incorporação abaixo:",Embed:"Incorporar",Media:"imagem","Nonbreaking space":"Espaço não separável","Page break":"Quebra de página","Paste as text":"Colar como texto",Preview:"Pré-visualizar",Print:"Imprimir",Save:"Salvar",Find:"Localizar","Replace with":"Substituir por",Replace:"Substituir","Replace all":"Substituir tudo",Prev:"Anterior",Next:"Próximo","Find and replace":"Localizar e substituir","Could not find the specified string.":"Não foi possível encontrar o termo especificado","Match case":"Diferenciar maiúsculas e minúsculas","Whole words":"Palavras inteiras",Spellcheck:"Corretor ortográfico",Ignore:"Ignorar","Ignore all":"Ignorar tudo",Finish:"Finalizar","Add to Dictionary":"Adicionar ao Dicionário","Insert table":"Inserir tabela","Table properties":"Propriedades da tabela","Delete table":"Excluir tabela",Cell:"Célula",Row:"Linha",Column:"Coluna","Cell properties":"Propriedades da célula","Merge cells":"Agrupar células","Split cell":"Dividir célula","Insert row before":"Inserir linha antes","Insert row after":"Inserir linha depois","Delete row":"Excluir linha","Row properties":"Propriedades da linha","Cut row":"Recortar linha","Copy row":"Copiar linha","Paste row before":"Colar linha antes","Paste row after":"Colar linha depois","Insert column before":"Inserir coluna antes","Insert column after":"Inserir coluna depois","Delete column":"Excluir coluna",Cols:"Colunas",Rows:"Linhas",Width:"Largura",Height:"Altura","Cell spacing":"Espaçamento da célula","Cell padding":"Espaçamento interno da célula",Caption:"Legenda",Left:"Esquerdo",Center:"Centro",Right:"Direita","Cell type":"Tipo de célula",Scope:"Escopo",Alignment:"Alinhamento","H Align":"Alinhamento H","V Align":"Alinhamento V",Top:"Superior",Middle:"Meio",Bottom:"Inferior","Header cell":"Célula cabeçalho","Row group":"Agrupar linha","Column group":"Agrupar coluna","Row type":"Tipo de linha",Header:"Cabeçalho",Body:"Corpo",Footer:"Rodapé","Border color":"Cor da borda","Insert template":"Inserir modelo",Templates:"Modelos",Template:"Modelo","Text color":"Cor do texto","Background color":"Cor do fundo","Custom...":"Personalizado...","Custom color":"Cor personalizada","No color":"Nenhuma cor","Table of Contents":"índice de Conteúdo","Show blocks":"Mostrar blocos","Show invisible characters":"Exibir caracteres invisíveis","Words: {0}":"Palavras: {0}","{0} words":"{0} palavras",File:"Arquivo",Edit:"Editar",Insert:"Inserir",View:"Visualizar",Format:"Formatar",Table:"Tabela",Tools:"Ferramentas","Powered by {0}":"Distribuído por  {0}","Rich Text Area. Press ALT-F9 for menu. Press ALT-F10 for toolbar. Press ALT-0 for help":"Área de texto formatado. Pressione ALT-F9 para exibir o menu, ALT-F10 para exibir a barra de ferramentas ou ALT-0 para exibir a ajuda"})},b2df:function(e,t,a){},c7e5:function(e,t,a){"use strict";a.r(t),function(e,t){a("e260"),a("e6cf"),a("cca6"),a("a79d"),a("15f5"),a("4989"),a("cb1e"),a("8501"),a("f387"),a("5aa9"),a("3dec"),a("6fc1"),a("e562"),a("acd2"),a("3c51"),a("07d1"),a("84ec"),a("64d8"),a("6bd7"),a("b2df"),a("764b"),a("e3f1");var o=a("c1df");a("d2d4"),a("d8b4"),window.$=e,window.moment=o,window.autorModal(),window.refreshMask(),window.refreshDatePicker(),window.initTextRichEditor("texto-rico")}.call(this,a("1157"),a("1157"))},d8b4:function(e,t,a){(function(e){var t=t||{};t.jQuery=a("1157"),a("b0c0");var o=a("7037");(function(){var t,a,r,n,i,s,l,c,u;if(r={version:"2.3.3",name:"jQuery-runner"},!(l=e)||!l.fn)throw new Error("["+r.name+"] jQuery or jQuery-like library is required for this plugin to work");i={},n=function(e){return(e<10?"0":"")+e},u=1,s=function(){return"runner"+u++},c=function(e,t){return e["r"+t]||e["webkitR"+t]||e["mozR"+t]||e["msR"+t]||function(e){return setTimeout(e,30)}}(this,"equestAnimationFrame"),a=function(e,t){var a,o,r,i,s,l,c,u,d,h,p;for(u=[36e5,6e4,1e3,10],l=["",":",":","."],s="",i="",r=(t=t||{}).milliseconds,o=u.length,d=0,e<0&&(e=Math.abs(e),s="-"),a=h=0,p=u.length;h<p;a=++h)d=0,e>=(c=u[a])&&(e-=(d=Math.floor(e/c))*c),(d||a>1||i)&&(a!==o-1||r)&&(i+=(i?l[a]:"")+n(d));return s+i},t=function(){function e(t,a,o){var r;if(!(this instanceof e))return new e(t,a,o);this.items=t,r=this.id=s(),this.settings=l.extend({},this.settings,a),i[r]=this,t.each((function(e,t){l(t).data("runner",r)})),this.value(this.settings.startAt),(o||this.settings.autostart)&&this.start()}return e.prototype.running=!1,e.prototype.updating=!1,e.prototype.finished=!1,e.prototype.interval=null,e.prototype.total=0,e.prototype.lastTime=0,e.prototype.startTime=0,e.prototype.lastLap=0,e.prototype.lapTime=0,e.prototype.settings={autostart:!1,countdown:!1,stopAt:null,startAt:0,milliseconds:!0,format:null},e.prototype.value=function(e){this.items.each(function(t){return function(a,o){var r;r=(a=l(o)).is("input")?"val":"text",a[r](t.format(e))}}(this))},e.prototype.format=function(e){var t;return t=this.settings.format,(t=l.isFunction(t)?t:a)(e,this.settings)},e.prototype.update=function(){var e,t,a,o,r;this.updating||(this.updating=!0,a=this.settings,r=l.now(),o=a.stopAt,e=a.countdown,t=r-this.lastTime,this.lastTime=r,e?this.total-=t:this.total+=t,null!==o&&(e&&this.total<=o||!e&&this.total>=o)&&(this.total=o,this.finished=!0,this.stop(),this.fire("runnerFinish")),this.value(this.total),this.updating=!1)},e.prototype.fire=function(e){this.items.trigger(e,this.info())},e.prototype.start=function(){var e;this.running||(this.running=!0,this.startTime&&!this.finished||this.reset(),this.lastTime=l.now(),e=function(t){return function(){t.running&&(t.update(),c(e))}}(this),c(e),this.fire("runnerStart"))},e.prototype.stop=function(){this.running&&(this.running=!1,this.update(),this.fire("runnerStop"))},e.prototype.toggle=function(){this.running?this.stop():this.start()},e.prototype.lap=function(){var e,t;return e=(t=this.lastTime)-this.lapTime,this.settings.countdown&&(e=-e),(this.running||e)&&(this.lastLap=e,this.lapTime=t),t=this.format(this.lastLap),this.fire("runnerLap"),t},e.prototype.reset=function(e){var t;e&&this.stop(),t=l.now(),"number"!=typeof this.settings.startAt||this.settings.countdown||(t-=this.settings.startAt),this.startTime=this.lapTime=this.lastTime=t,this.total=this.settings.startAt,this.value(this.total),this.finished=!1,this.fire("runnerReset")},e.prototype.info=function(){var e;return e=this.lastLap||0,{running:this.running,finished:this.finished,time:this.total,formattedTime:this.format(this.total),startTime:this.startTime,lapTime:e,formattedLapTime:this.format(e),settings:this.settings}},e}(),l.fn.runner=function(e,a,n){var s,c;switch(e||(e="init"),"object"===o(e)&&(n=a,a=e,e="init"),c=!!(s=this.data("runner"))&&i[s],e){case"init":new t(this,a,n);break;case"info":if(c)return c.info();break;case"reset":c&&c.reset(a);break;case"lap":if(c)return c.lap();break;case"start":case"stop":case"toggle":if(c)return c[e]();break;case"version":return r.version;default:l.error("["+r.name+"] Method "+e+" does not exist")}return this},l.fn.runner.format=a}).call(t)}).call(this,a("1157"))},e3f1:function(e,t,a){"use strict";(function(e,t){a("4160"),a("ac1f"),a("1276"),a("498a"),a("159b");var o=a("571b"),r=a.n(o);window.removeTinymce=function(){for(;window.tinymce.editors.length>0;)window.tinymce.remove(window.tinymce.editors[0])},window.initTextRichEditor=function(e){var t=arguments.length>1&&void 0!==arguments[1]&&arguments[1];window.removeTinymce();var a={force_br_newlines:!1,force_p_newlines:!1,forced_root_block:"",content_style:r.a.contentStyle,skin:!1,plugins:["lists table code"],menubar:"file edit view format table tools",toolbar:"undo redo | styleselect | bold italic | alignleft aligncenter alignright alignjustify | bullist numlist outdent indent",min_height:200};t&&(a.readonly=1,a.menubar=!1,a.toolbar=!1),null!=e?(a.elements=e,a.mode="exact"):a.mode="textareas",r.a.use(),window.tinymce.init(a)},window.refreshDatePicker=function(){e.datepicker.setDefaults(e.datepicker.regional["pt-BR"]),e(".dateinput").datepicker();var a=document.querySelectorAll(".dateinput");t.each(a,(function(e,t){e.setAttribute("autocomplete","off")}))},window.getCookie=function(t){var a=null;if(document.cookie&&""!==document.cookie)for(var o=document.cookie.split(";"),r=0;r<o.length;r++){var n=e.trim(o[r]);if(n.substring(0,t.length+1)===t+"="){a=decodeURIComponent(n.substring(t.length+1));break}}return a},window.autorModal=function(){e((function(){var t=e("#modal_autor").dialog({autoOpen:!1,modal:!0,width:500,height:340,show:{effect:"blind",duration:500},hide:{effect:"explode",duration:500}});e("#button-id-limpar").click((function(){function t(t){e(t).length>0&&e(t).val("")}e("#nome_autor").text(""),t("#id_autor"),t("#id_autoria__autor"),t("#id_autorianorma__autor")})),e("#button-id-pesquisar").click((function(){e("#q").val(""),e("#div-resultado").children().remove(),e("#modal_autor").dialog("open"),e("#selecionar").attr("hidden","hidden")})),e("#pesquisar").click((function(){var a=e("#q").val();e.get("/api/autor?q="+a,(function(a){if(e("#div-resultado").children().remove(),0===a.pagination.total_entries)return e("#selecionar").attr("hidden","hidden"),void e("#div-resultado").html("<span class='alert'><strong>Nenhum resultado</strong></span>");var o=e('<select id="resultados" style="min-width: 90%; max-width:90%;" size="5"/>');a.results.forEach((function(t){o.append(e("<option>").attr("value",t.value).text(t.text))})),e("#div-resultado").append("<br/>").append(o),e("#selecionar").removeAttr("hidden","hidden"),a.pagination.total_pages>1&&e("#div-resultado").prepend("<span><br/>Mostrando 10 primeiros autores relativos a sua busca.<br/></span>"),e("#selecionar").click((function(){var a=e("#resultados option:selected"),o=a.val(),r=a.text();e("#nome_autor").text(r),e("#id_autoria__autor").length&&e("#id_autoria__autor").val(o),e("#id_autor").length&&e("#id_autor").val(o),e("#id_autorianorma__autor").length&&e("#id_autorianorma__autor").val(o),t.dialog("close")}))}))}))}))},window.refreshMask=function(){e(".telefone").mask("(99) 9999-9999",{placeholder:"(__) ____ -____"}),e(".cpf").mask("000.000.000-00",{placeholder:"___.___.___-__"}),e(".cep").mask("00000-000",{placeholder:"_____-___"}),e(".rg").mask("0.000.000",{placeholder:"_.___.___"}),e(".titulo_eleitor").mask("0000.0000.0000.0000",{placeholder:"____.____.____.____"}),e(".dateinput").mask("00/00/0000",{placeholder:"__/__/____"}),e(".hora, input[name=hora_inicio], input[name=hora_fim], input[name=hora]").mask("00:00",{placeholder:"hh:mm"}),e(".hora_hms").mask("00:00:00",{placeholder:"hh:mm:ss"}),e(".timeinput").mask("00:00:00",{placeholder:"hh:mm:ss"}),e(".cronometro").mask("00:00:00",{placeholder:"hh:mm:ss"})}}).call(this,a("1157"),a("2ef0"))},e4b3:function(e,t,a){}});
//# sourceMappingURL=global.5d74141e.js.map