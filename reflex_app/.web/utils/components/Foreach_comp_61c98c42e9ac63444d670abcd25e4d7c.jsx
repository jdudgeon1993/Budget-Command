
import {Fragment,memo,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {Box as RadixThemesBox,Flex as RadixThemesFlex,Text as RadixThemesText} from "@radix-ui/themes"
import {jsx} from "@emotion/react"






export const Foreach_comp_61c98c42e9ac63444d670abcd25e4d7c = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)
const [addEvents, connectErrors] = useContext(EventLoopContext);



    return(
        Array.prototype.map.call(reflex___state____state__cura___state____app_state.archived_cat_rows_rx_state_ ?? [],((row_rx_state_,index_caa5d9cbba1f42a8bb75c6f66e02da2a)=>(jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["background"] : "#14141c", ["border"] : "1px dashed #252535", ["borderRadius"] : "8px", ["padding"] : "8px 12px", ["marginBottom"] : "5px", ["opacity"] : "0.7", ["alignItems"] : "center", ["width"] : "100%", ["gap"] : "8px" }),direction:"row",key:index_caa5d9cbba1f42a8bb75c6f66e02da2a,gap:"3"},jsx(RadixThemesBox,{css:({ ["width"] : "10px", ["height"] : "10px", ["borderRadius"] : "50%", ["background"] : row_rx_state_?.["color"], ["flexShrink"] : "0" })},),jsx(RadixThemesText,{as:"p",css:({ ["flex"] : "1", ["fontSize"] : "13px", ["color"] : "#6868a2", ["fontStyle"] : "italic" })},row_rx_state_?.["name"]),jsx(RadixThemesBox,{css:({ ["fontSize"] : "11px", ["color"] : "#34d399", ["cursor"] : "pointer", ["padding"] : "3px 8px", ["borderRadius"] : "4px", ["border"] : "1px solid #34d39944", ["&:hover"] : ({ ["background"] : "#34d39911" }), ["fontFamily"] : "'Share Tech Mono', monospace", ["--default-font-family"] : "'Share Tech Mono', monospace", ["flexShrink"] : "0" }),onClick:((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.unarchive_category", ({ ["cid"] : row_rx_state_?.["id"] }), ({  })))], [_e], ({  }))))},"Restore")))))
    )
});
