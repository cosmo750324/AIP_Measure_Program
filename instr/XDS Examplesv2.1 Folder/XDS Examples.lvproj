<?xml version='1.0' encoding='UTF-8'?>
<Project Type="Project" LVVersion="13008000">
	<Item Name="My Computer" Type="My Computer">
		<Property Name="server.app.propertiesEnabled" Type="Bool">true</Property>
		<Property Name="server.control.propertiesEnabled" Type="Bool">true</Property>
		<Property Name="server.tcp.enabled" Type="Bool">false</Property>
		<Property Name="server.tcp.port" Type="Int">0</Property>
		<Property Name="server.tcp.serviceName" Type="Str">My Computer/VI Server</Property>
		<Property Name="server.tcp.serviceName.default" Type="Str">My Computer/VI Server</Property>
		<Property Name="server.vi.callsEnabled" Type="Bool">true</Property>
		<Property Name="server.vi.propertiesEnabled" Type="Bool">true</Property>
		<Property Name="specify.custom.address" Type="Bool">false</Property>
		<Item Name="Example" Type="Folder">
			<Item Name="acquire multi waves by LAN.vi" Type="VI" URL="../Example/acquire multi waves by LAN.vi"/>
			<Item Name="acquire multi waves.vi" Type="VI" URL="../Example/acquire multi waves.vi"/>
			<Item Name="acquire single wave by LAN.vi" Type="VI" URL="../Example/acquire single wave by LAN.vi"/>
			<Item Name="acquire single wave.vi" Type="VI" URL="../Example/acquire single wave.vi"/>
			<Item Name="XDSBMPread.vi" Type="VI" URL="../Example/XDSBMPread.vi"/>
		</Item>
		<Item Name="subvi" Type="Folder">
			<Item Name="acquire multi waves by LAN init subvi.vi" Type="VI" URL="../Subvi/acquire multi waves by LAN init subvi.vi"/>
			<Item Name="acquire multi waves by LAN subvi.vi" Type="VI" URL="../Subvi/acquire multi waves by LAN subvi.vi"/>
			<Item Name="acquire multi waves init subvi.vi" Type="VI" URL="../Subvi/acquire multi waves init subvi.vi"/>
			<Item Name="acquire multi waves subvi.vi" Type="VI" URL="../Subvi/acquire multi waves subvi.vi"/>
			<Item Name="acquire single wave by LAN init subvi.vi" Type="VI" URL="../Subvi/acquire single wave by LAN init subvi.vi"/>
			<Item Name="acquire single wave by LAN subvi.vi" Type="VI" URL="../Subvi/acquire single wave by LAN subvi.vi"/>
			<Item Name="acquire single wave init subvi.vi" Type="VI" URL="../Subvi/acquire single wave init subvi.vi"/>
			<Item Name="acquire single wave subvi.vi" Type="VI" URL="../Subvi/acquire single wave subvi.vi"/>
			<Item Name="readScreenBmp subvi.vi" Type="VI" URL="../Subvi/readScreenBmp subvi.vi"/>
		</Item>
		<Item Name="Dependencies" Type="Dependencies">
			<Item Name="vi.lib" Type="Folder">
				<Item Name="Calc Long Word Padded Width.vi" Type="VI" URL="/&lt;vilib&gt;/picture/bmp.llb/Calc Long Word Padded Width.vi"/>
				<Item Name="Draw Flattened Pixmap.vi" Type="VI" URL="/&lt;vilib&gt;/picture/picture.llb/Draw Flattened Pixmap.vi"/>
				<Item Name="ex_CorrectErrorChain.vi" Type="VI" URL="/&lt;vilib&gt;/express/express shared/ex_CorrectErrorChain.vi"/>
				<Item Name="FixBadRect.vi" Type="VI" URL="/&lt;vilib&gt;/picture/pictutil.llb/FixBadRect.vi"/>
				<Item Name="Flip and Pad for Picture Control.vi" Type="VI" URL="/&lt;vilib&gt;/picture/bmp.llb/Flip and Pad for Picture Control.vi"/>
				<Item Name="imagedata.ctl" Type="VI" URL="/&lt;vilib&gt;/picture/picture.llb/imagedata.ctl"/>
				<Item Name="Read BMP File Data.vi" Type="VI" URL="/&lt;vilib&gt;/picture/bmp.llb/Read BMP File Data.vi"/>
				<Item Name="Read BMP File.vi" Type="VI" URL="/&lt;vilib&gt;/picture/bmp.llb/Read BMP File.vi"/>
				<Item Name="Read BMP Header Info.vi" Type="VI" URL="/&lt;vilib&gt;/picture/bmp.llb/Read BMP Header Info.vi"/>
				<Item Name="subDisplayMessage.vi" Type="VI" URL="/&lt;vilib&gt;/express/express output/DisplayMessageBlock.llb/subDisplayMessage.vi"/>
			</Item>
		</Item>
		<Item Name="Build Specifications" Type="Build"/>
	</Item>
</Project>
