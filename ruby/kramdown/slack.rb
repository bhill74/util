require 'kramdown/converter/base'
require 'pp'
require 'json'

module Kramdown
    module Converter
        class Slack < Base
            def convert(root)
                r = cleanup_ast(root).map { |child|
                    #pp child
                    convert_element(child)
                }.compact.flatten
                #pp r
                r.to_json 
            end

            private

            def cleanup_ast(root)
                remove_blanks(root)
                root.children.map do |child|
                    elements = []
                    extract_non_nestable_elements(child, elements)
                    [child, elements]
                end.flatten.compact
            end

            def remove_blanks(root)
                root.children = root.children.inject([]) do |memo, child|
                    unless child.type == :blank
                        remove_blanks(child)
                        memo << child
                    end
                    memo
                end
            end

            def extract_non_nestable_elements(child, elements)
                child.children = child.children.inject([]) do |memo, element|
                    if element.type == :img
                        elements << element
                        warning('images inside content will be moved to the top level and may be rendered differently') if child.children.size > 1
                    elsif element.type == :ul
                        warning('nested list moved to the top level')
                        elements << element
                        extract_non_nestable_elements(element, elements)
                    else
                        memo << element
                        extract_non_nestable_elements(element, elements)
                    end
                    memo
                end
            end
                        
            def convert_element(element)
                send("convert_#{element.type}", element)
            end
                        
            def convert_header(element)
                level = "-" * element.options[:level]
                {
                    type: "section",
                    text: {
                        type: "mrkdwn",
                        text: "*#{level}#{extract_text(element).strip}#{level}*"
                    }
                }
            end
                        
            def convert_p(element)
                return nil if element.children.size == 0
                {
                    type: "section",
                    text: {
                        type: "mrkdwn",
                        text: extract_text(element)
                    }
                }
            end
                        
            def convert_ol(element)
                {
                    type: "section",
                    text: {
                        type: "mrkdwn",
                        text: convert_list(element, '#').join("\n")
                    }
                }
            end
                        
            def convert_ul(element)
                {
                    type: "section",
                    text: {
                        type: "mrkdwn",
                        text: convert_list(element, '-').join("\n")
                    }
                }
            end
                        
            def convert_list(element, type)
                i = 0
                element.children.map do |child|
                    i += 1
                    prefix = (type == '#') ? "#{i}." : type
                    convert_li(prefix, child)
                end
            end
                        
            def convert_li(prefix, element)
                "#{prefix}#{extract_text(element)}"
            end
                        
            def convert_codeblock(element)
                {
                    type: "section",
                    text: {
                        type: "mrkdwn",
                        text: "```#{extract_text(element)}```"
                    }
                }
            end
                        
            def convert_blockquote(element)
                ">#{extract_text(element)}>"
            end
                        
            def convert_hr(element)
                warning('translating hr elements is not supported')
                nil
            end
                        
            def convert_img(element)
                {
                    type: 'image',
                    content: {
                        text: '',
                        spans: []
                    },
                    data: {
                        origin: {
                            url: element.attr["src"]
                        },
                        alt: element.attr["alt"]
                    }
                }
            end
                        
            def convert_html_element(element)
                warning('translating html elements is not supported')
                nil
            end
            
            def reduce_to(items, size)
                result = []
                n = size-1
                n.times do |i|
                    result << items[i]
                end
                result << items[n..-1].join("/")
            end

            def convert_table(element)
                fields = []
                headers = element.children[0].children[0].children.map {|child| extract_text(child).strip}
                headers = reduce_to(headers, 2)
                fields += headers.map do |h| 
                    {
                        type: "mrkdwn",
                        text: "*#{h}*"
                    } 
                end
                element.children[1].children.each do |row|
                    cells = row.children.map {|child| extract_text(child)}
                    cells = reduce_to(cells, 2)
                    fields += cells.map do |c|
                        {
                            type: "mrkdwn",
                            text: c
                        }
                    end
                end

                result = [] 
                while fields.any?
                    st = {type: "section", fields: fields.shift(10)}
                    result.push(st)
                end

                result
            end

            def convert_dl(element)
                warning('translating dl is not supported')
                nil
            end
                        
            def convert_math(element)
                warning('translating math is not supported')
                nil
            end
            
            def convert_comment(element)
                warning('translating comment is not supported')
                nil
            end
                        
            def convert_xml_comment(element)
                warning('translating xml_comment is not supported')
                nil
            end
                        
            def convert_xml_pi(element)
                warning('translating xml_pi is not supported')
                nil
            end

            def convert_raw(element)
                warning('translating raw is not supported')
                nil
            end

            def extract_text(element)
                text = element.value.nil? ? "" : element.value
                element.children.each do |child|
                    text += send("extract_span2_#{child.type}", child)
                end
                text 
            end

            def extract_content(element, memo={text: '', spans: []})
                element.children.inject(memo) do |memo2, child|
                    send("extract_span_#{child.type}", child, memo2)
                    memo2
                end
            end

            def insert_span(element, memo, span)
                span[:start] = memo[:text].size
                extract_content(element, memo)
                span[:end] = memo[:text].size
                memo[:spans] << span
                memo
            end

            def extract_span2_text(element)
                element.value
            end

            def extract_span_text(element, memo)
                memo[:text] += element.value
                memo
            end
                        
            def extract_span_a(element, memo)
                insert_span(element, memo, {
                    type: 'hyperlink',
                    data: {
                        url: element.attr["href"]
                    }
                })
            end
 
            def extract_span_strong(element, memo)
                insert_span(element, memo, {
                    type: 'strong'
                })
            end

            def span2_format(element,formatter)
                f = method(formatter)
                text = ""
                if (element.respond_to?(:children) && element.children.length > 0)
                    text = 
                        element.children
                        .map{ |child| f.call(child.value) }
                            .join(' ')
                elsif (element.respond_to?(:value))
                    text = f.call(element.value) 
                end
            end

            def text_formatter(text)
                text
            end

            def strong_formatter(text)
                "*#{text}*"
            end

            def code_formatter(text)
                "`#{text}`"
            end

            def em_formatter(text)
                "_#{text}_"
            end

            def smart_quote_formatter(text)
                text == :lsquo ? '`' : '\'' 
            end

            def typographic_formatter(text)
                text.to_s
            end

            def extract_span2_text(element)
                span2_format(element, :text_formatter)
            end

            def extract_span2_em(element)
                span2_format(element, :em_formatter)
            end

            def extract_span2_strong(element)
                span2_format(element, :strong_formatter)
            end

            def extract_span2_smart_quote(element)
                span2_format(element, :smart_quote_formatter)
            end

            def extract_span2_codespan(element)
                span2_format(element, :code_formatter)
            end

            def extract_span2_typographic_sym(element)
                span2_format(element, :typographic_formatter)
            end

            def extract_span_em(element, memo)
                insert_span(element, memo, {
                    type: 'em'
                })
            end
            
            def extract_span2_p(element)
                {
                    type: "section",
                    text: {
                        type: "mrkdwn",
                        text: extract_text(element)
                    }
                }
            end

            def extract_span_p(element, memo)
                extract_content(element, memo)
            end
            
            def extract_span_br(element, memo)
                memo[:text] += "\n"
            end
            
            def extract_span_html_element(element, memo)
                warning('translating html elements is not supported')
            end
                        
            def extract_span_footnote(element, memo)
                warning('translating footnote is not supported')
            end
                        
            def extract_span_abbreviation(element, memo)
                warning('translating abbreviation is not supported')
                memo[:text] += element.value
            end
                        
            TYPOGRAPHIC_SYMS = {
                mdash: [::Kramdown::Utils::Entities.entity('mdash')],
                ndash: [::Kramdown::Utils::Entities.entity('ndash')],
                hellip: [::Kramdown::Utils::Entities.entity('hellip')],
                laquo_space: [::Kramdown::Utils::Entities.entity('laquo'), ::Kramdown::Utils::Entities.entity('nbsp')],
                raquo_space: [::Kramdown::Utils::Entities.entity('nbsp'), ::Kramdown::Utils::Entities.entity('raquo')],
                laquo: [::Kramdown::Utils::Entities.entity('laquo')],
                raquo: [::Kramdown::Utils::Entities.entity('raquo')]
            }

            def extract_span_typographic_sym(element, memo)
                value = TYPOGRAPHIC_SYMS[element.value].map {|e| e.char }.join('')
                memo[:text] += value
            end
                        
            def extract_span_entity(element, memo)
                memo[:text] += element.value.char
            end

            def extract_span_smart_quote(element, memo)
                memo[:text] += ::Kramdown::Utils::Entities.entity(element.value.to_s).char
            end
        end
    end
end
